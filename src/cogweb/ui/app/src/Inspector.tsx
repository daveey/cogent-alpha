import { useState } from "react";
import type { CogWebNodeData, WSOutgoing } from "./types";
import "./inspector.css";

interface Props {
  node: CogWebNodeData | null;
  allNodes: Record<string, CogWebNodeData>;
  send: (msg: WSOutgoing) => void;
}

export default function Inspector({ node, allNodes, send }: Props) {
  const [cmdType, setCmdType] = useState("");
  const [cmdData, setCmdData] = useState("");

  if (!node) {
    return (
      <div className="inspector">
        <div className="inspector-header">Inspector</div>
        <div className="inspector-empty">Select a node to inspect</div>
      </div>
    );
  }

  const handleGuide = () => {
    if (!cmdType.trim()) return;
    let parsed: unknown = cmdData.trim() || undefined;
    try {
      if (cmdData.trim()) parsed = JSON.parse(cmdData);
    } catch {
      // send as string
    }
    send({ type: "guide", node_id: node.node_id, command: cmdType.trim(), data: parsed });
    setCmdType("");
    setCmdData("");
  };

  return (
    <div className="inspector">
      <div className="inspector-header">Inspector</div>

      {/* Identity */}
      <Section title="Identity">
        <Field label="Class" value={node.class_name} />
        <Field label="ID" value={node.node_id} mono small />
        <Field label="Status">
          <span className={`status-badge ${node.status}`}>{node.status}</span>
        </Field>
        {node.parent_id && (
          <Field label="Parent" value={parentName(node.parent_id, allNodes)} mono small />
        )}
      </Section>

      {/* Mixins */}
      {node.mixins.length > 0 && (
        <Section title="Mixins">
          <div className="tag-list">
            {node.mixins.map((m) => (
              <span key={m} className="insp-tag mixin">{m}</span>
            ))}
          </div>
        </Section>
      )}

      {/* Handlers */}
      {(node.listen_channels.length > 0 || node.enact_commands.length > 0) && (
        <Section title="Handlers">
          <div className="tag-list">
            {node.listen_channels.map((ch) => (
              <span key={ch} className="insp-tag listen">@listen {ch}</span>
            ))}
            {node.enact_commands.map((cmd) => (
              <span key={cmd} className="insp-tag enact">@enact {cmd}</span>
            ))}
          </div>
        </Section>
      )}

      {/* Channels */}
      {Object.keys(node.channels).length > 0 && (
        <Section title="Channels">
          {Object.entries(node.channels).map(([ch, n]) => (
            <Field key={ch} label={ch} value={`${n} sub${n !== 1 ? "s" : ""}`} />
          ))}
        </Section>
      )}

      {/* Children */}
      {node.children.length > 0 && (
        <Section title={`Children (${node.children.length})`}>
          {node.children.map((cid) => (
            <Field key={cid} label="" value={parentName(cid, allNodes)} mono small />
          ))}
        </Section>
      )}

      {/* Config */}
      {Object.keys(node.config).length > 0 && (
        <Section title="Config">
          {Object.entries(node.config).map(([k, v]) => (
            <Field key={k} label={k} value={String(v)} />
          ))}
        </Section>
      )}

      {/* Guide command */}
      <Section title="Send Command">
        <div className="guide-form">
          <input
            className="guide-input"
            placeholder="command type"
            value={cmdType}
            onChange={(e) => setCmdType(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleGuide()}
          />
          <input
            className="guide-input"
            placeholder='data (JSON or string)'
            value={cmdData}
            onChange={(e) => setCmdData(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleGuide()}
          />
          <button className="guide-btn" onClick={handleGuide} disabled={!cmdType.trim()}>
            Guide
          </button>
        </div>
        {node.enact_commands.length > 0 && (
          <div className="quick-cmds">
            {node.enact_commands.map((cmd) => (
              <button
                key={cmd}
                className="quick-cmd"
                onClick={() => {
                  send({ type: "guide", node_id: node.node_id, command: cmd });
                }}
              >
                {cmd}
              </button>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="insp-section">
      <div className="insp-section-title">{title}</div>
      {children}
    </div>
  );
}

function Field({
  label,
  value,
  mono,
  small,
  children,
}: {
  label: string;
  value?: string;
  mono?: boolean;
  small?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className="insp-field">
      {label && <span className="insp-label">{label}</span>}
      {children ?? (
        <span
          className={`insp-value${mono ? " mono" : ""}${small ? " small" : ""}`}
        >
          {value}
        </span>
      )}
    </div>
  );
}

function parentName(id: string, all: Record<string, CogWebNodeData>): string {
  const n = all[id];
  return n ? n.class_name : id.slice(0, 20) + "\u2026";
}
