import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import type { CogWebNodeData } from "./types";
import "./coglet-node.css";

type CogletNodeType = Node<CogWebNodeData>;

export default function CogletNode({ data, selected }: NodeProps<CogletNodeType>) {
  const statusClass =
    data.status === "error"
      ? "status-error"
      : data.status === "stopped"
        ? "status-stopped"
        : "";

  return (
    <div
      className={`coglet-node ${statusClass} ${selected ? "selected" : ""}`}
    >
      {/* Target handle (top) — parent connects here */}
      <Handle type="target" position={Position.Top} id="parent" />

      <div className="node-header">
        <div className="node-title">
          <span className="class-name">{data.class_name}</span>
          <span className={`status-dot ${data.status}`} title={data.status} />
        </div>
        <div className="node-id">{shortId(data.node_id)}</div>
      </div>

      <div className="node-body">
        {/* Mixins */}
        {data.mixins.length > 0 && (
          <div className="mixin-row">
            {data.mixins.map((m) => (
              <span key={m} className="tag mixin">
                {m}
              </span>
            ))}
          </div>
        )}

        {/* Ports */}
        <div className="ports-row">
          {/* Inputs: @listen + @enact */}
          <div className="port-col left">
            {data.listen_channels.map((ch) => (
              <div key={`l-${ch}`} className="port">
                <Handle
                  type="target"
                  position={Position.Left}
                  id={`listen-${ch}`}
                  className="port-handle listen"
                />
                <span className="port-label listen">{ch}</span>
              </div>
            ))}
            {data.enact_commands.map((cmd) => (
              <div key={`e-${cmd}`} className="port">
                <Handle
                  type="target"
                  position={Position.Left}
                  id={`enact-${cmd}`}
                  className="port-handle enact"
                />
                <span className="port-label enact">{cmd}</span>
              </div>
            ))}
          </div>

          {/* Outputs: transmit channels */}
          <div className="port-col right">
            {Object.entries(data.channels as Record<string, number>).map(([ch, subs]) => (
              <div key={`t-${ch}`} className="port">
                <span className="port-label transmit">
                  {ch}
                  <span className="sub-count">{subs}</span>
                </span>
                <Handle
                  type="source"
                  position={Position.Right}
                  id={`transmit-${ch}`}
                  className="port-handle transmit"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Config summary */}
        {typeof data.config.restart === "string" && data.config.restart !== "never" && (
          <div className="config-row">
            <span className="tag config">
              restart: {data.config.restart}
            </span>
          </div>
        )}
      </div>

      {/* Source handle (bottom) — connects to children */}
      <Handle type="source" position={Position.Bottom} id="child" />
    </div>
  );
}

function shortId(id: string): string {
  return id.length > 24 ? id.slice(0, 24) + "\u2026" : id;
}
