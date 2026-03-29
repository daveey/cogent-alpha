import { useCallback, useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Panel,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import CogletNodeComponent from "./CogletNode";
import Inspector from "./Inspector";
import { useWebSocket } from "./useWebSocket";
import type { CogWebSnapshot, CogWebNodeData, WSOutgoing } from "./types";
import "./app.css";

type CogletNode = Node<CogWebNodeData>;
type CogletEdge = Edge;

const NODE_TYPES = { coglet: CogletNodeComponent };

const EDGE_DEFAULTS = {
  data: { stroke: "#58a6ff", strokeWidth: 1.5, animated: true },
  control: { stroke: "#f85149", strokeWidth: 1.5, strokeDasharray: "6 3" },
  observe: { stroke: "#8b949e", strokeWidth: 1, strokeDasharray: "2 2" },
};

function snapshotToFlow(
  snap: CogWebSnapshot,
  prevPositions: Map<string, { x: number; y: number }>,
): { nodes: CogletNode[]; edges: CogletEdge[]; positions: Map<string, { x: number; y: number }> } {
  const nodeEntries = Object.entries(snap.nodes);
  const positions = new Map(prevPositions);

  // Hierarchical layout: BFS from roots
  const childrenOf = new Map<string, string[]>();
  const hasParent = new Set<string>();
  for (const [nid, node] of nodeEntries) {
    const kids = (node.children || []).filter((c) => snap.nodes[c]);
    childrenOf.set(nid, kids);
    for (const c of kids) hasParent.add(c);
  }
  const roots = nodeEntries.filter(([nid]) => !hasParent.has(nid)).map(([nid]) => nid);
  if (roots.length === 0 && nodeEntries.length > 0) roots.push(nodeEntries[0][0]);

  // Assign levels via BFS
  const levels = new Map<string, number>();
  const queue: [string, number][] = roots.map((r) => [r, 0]);
  const visited = new Set<string>();
  while (queue.length > 0) {
    const [nid, level] = queue.shift()!;
    if (visited.has(nid)) continue;
    visited.add(nid);
    levels.set(nid, level);
    for (const c of childrenOf.get(nid) || []) queue.push([c, level + 1]);
  }
  // Orphans
  let maxLevel = Math.max(0, ...levels.values());
  for (const [nid] of nodeEntries) {
    if (!levels.has(nid)) levels.set(nid, ++maxLevel);
  }

  // Group by level and position
  const byLevel = new Map<number, string[]>();
  for (const [nid, lvl] of levels) {
    if (!byLevel.has(lvl)) byLevel.set(lvl, []);
    byLevel.get(lvl)!.push(nid);
  }

  const nodeW = 220;
  const nodeH = 160;
  const gapX = 80;
  const gapY = 100;

  for (const [lvl, row] of [...byLevel.entries()].sort(([a], [b]) => a - b)) {
    const totalW = row.length * nodeW + (row.length - 1) * gapX;
    const startX = -totalW / 2 + nodeW / 2;
    for (let i = 0; i < row.length; i++) {
      const nid = row[i];
      if (!positions.has(nid)) {
        positions.set(nid, {
          x: startX + i * (nodeW + gapX),
          y: lvl * (nodeH + gapY),
        });
      }
    }
  }

  // Build React Flow nodes
  const nodes: CogletNode[] = nodeEntries.map(([nid, nodeData]) => {
    const pos = positions.get(nid) || { x: 0, y: 0 };
    return {
      id: nid,
      type: "coglet",
      position: pos,
      data: nodeData,
    };
  });

  // Build edges: hierarchy (child links) + explicit edges
  const edges: CogletEdge[] = [];
  const edgeSet = new Set<string>();

  // Hierarchy edges (parent → child)
  for (const [nid, node] of nodeEntries) {
    for (const cid of node.children || []) {
      if (!snap.nodes[cid]) continue;
      const key = `${nid}->child->${cid}`;
      if (edgeSet.has(key)) continue;
      edgeSet.add(key);
      edges.push({
        id: key,
        source: nid,
        target: cid,
        sourceHandle: "child",
        targetHandle: "parent",
        style: EDGE_DEFAULTS.control,
        label: "supervise",
        labelStyle: { fill: "#8b949e", fontSize: 9 },
      });
    }
  }

  // Explicit edges from registry
  for (const edge of snap.edges || []) {
    const key = `${edge.from}->${edge.channel}->${edge.to}`;
    if (edgeSet.has(key)) continue;
    edgeSet.add(key);
    const kind = edge.kind || "data";
    const style = EDGE_DEFAULTS[kind as keyof typeof EDGE_DEFAULTS] || EDGE_DEFAULTS.data;
    edges.push({
      id: key,
      source: edge.from,
      target: edge.to,
      style,
      animated: kind === "data",
      label: edge.channel,
      labelStyle: { fill: "#8b949e", fontSize: 9 },
    });
  }

  return { nodes, edges, positions };
}

function FlowInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState<CogletNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<CogletEdge>([]);
  const [selectedNode, setSelectedNode] = useState<CogWebNodeData | null>(null);
  const [allNodeData, setAllNodeData] = useState<Record<string, CogWebNodeData>>({});
  const [connected, setConnected] = useState(false);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);
  const [showInspector, setShowInspector] = useState(true);
  const positionsRef = useRef<Map<string, { x: number; y: number }>>(new Map());
  const { fitView } = useReactFlow();
  const fitPending = useRef(false);
  const sendRef = useRef<(msg: WSOutgoing) => void>(() => {});

  const handleSnapshot = useCallback(
    (snap: CogWebSnapshot) => {
      const { nodes: flowNodes, edges: flowEdges, positions } = snapshotToFlow(
        snap,
        positionsRef.current,
      );
      positionsRef.current = positions;
      setNodes(flowNodes);
      setEdges(flowEdges);
      setAllNodeData(snap.nodes);
      setNodeCount(flowNodes.length);
      setEdgeCount(flowEdges.length);

      // Update selected node data if still exists
      setSelectedNode((prev) => {
        if (prev && snap.nodes[prev.node_id]) return snap.nodes[prev.node_id];
        return prev;
      });

      // Fit view on first snapshot
      if (!fitPending.current && flowNodes.length > 0) {
        fitPending.current = true;
        setTimeout(() => fitView({ padding: 0.15, duration: 300 }), 100);
      }
    },
    [setNodes, setEdges, fitView],
  );

  const { connected: wsConnected, send } = useWebSocket(handleSnapshot);
  sendRef.current = send;

  useEffect(() => {
    setConnected(wsConnected);
  }, [wsConnected]);

  // Also fetch initial snapshot via REST
  useEffect(() => {
    fetch("/api/graph")
      .then((r) => r.json())
      .then((data) => {
        if (Object.keys(data.nodes || {}).length > 0) {
          handleSnapshot(data);
        }
      })
      .catch(() => {});
  }, [handleSnapshot]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: CogletNode) => {
      setSelectedNode(allNodeData[node.id] || null);
    },
    [allNodeData],
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Track manual node drags
  const onNodeDragStop = useCallback(
    (_: React.MouseEvent, node: CogletNode) => {
      positionsRef.current.set(node.id, { ...node.position });
    },
    [],
  );

  return (
    <div className="cogweb-app">
      {/* Header */}
      <div className="cogweb-header">
        <span className="cogweb-title">CogWeb</span>
        <span className={`conn-status ${connected ? "on" : ""}`}>
          {connected ? "connected" : "disconnected"}
        </span>
        <div style={{ flex: 1 }} />
        <button className="hdr-btn" onClick={() => fitView({ padding: 0.15, duration: 300 })}>
          Fit
        </button>
        <button className="hdr-btn" onClick={() => send({ type: "refresh" })}>
          Refresh
        </button>
        <button className="hdr-btn" onClick={() => setShowInspector((v) => !v)}>
          Inspector
        </button>
      </div>

      {/* Main area */}
      <div className="cogweb-main">
        <div className="cogweb-canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onNodeDragStop={onNodeDragStop}
            nodeTypes={NODE_TYPES}
            fitView
            snapToGrid
            snapGrid={[20, 20]}
            minZoom={0.05}
            maxZoom={3}
            defaultEdgeOptions={{ type: "smoothstep" }}
            proOptions={{ hideAttribution: true }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#21262d" />
            <Controls
              showInteractive={false}
              style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8 }}
            />
            <MiniMap
              nodeStrokeColor={(n) => {
                const d = n.data as unknown as CogWebNodeData;
                if (d.status === "error") return "#f85149";
                if (d.status === "stopped") return "#8b949e";
                return "#3fb950";
              }}
              nodeColor={() => "#161b22"}
              maskColor="rgba(13,17,23,0.8)"
              style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 8 }}
            />
            <Panel position="bottom-center">
              <div className="stats-bar">
                <span>Nodes: {nodeCount}</span>
                <span>Edges: {edgeCount}</span>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {showInspector && (
          <Inspector node={selectedNode} allNodes={allNodeData} send={send} />
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FlowInner />
    </ReactFlowProvider>
  );
}
