/** Wire types matching the Python CogWebSnapshot / CogWebNode. */

export interface CogWebNodeData extends Record<string, unknown> {
  node_id: string;
  class_name: string;
  mixins: string[];
  channels: Record<string, number>;
  listen_channels: string[];
  enact_commands: string[];
  children: string[];
  parent_id: string | null;
  config: Record<string, unknown>;
  status: "running" | "stopped" | "error";
  updated_at: number;
}

export interface CogWebEdge {
  from: string;
  to: string;
  channel: string;
  kind: "data" | "control" | "observe";
}

export interface CogWebSnapshot {
  nodes: Record<string, CogWebNodeData>;
  edges: CogWebEdge[];
}

/** WebSocket message types. */
export type WSIncoming =
  | { type: "snapshot"; data: CogWebSnapshot }
  | { type: "pong" }
  | { type: "guide_result"; node_id: string; ok: boolean; error?: string }
  | { type: "status_updated"; node_id: string; status: string }
  | { type: "error"; data: string };

export type WSOutgoing =
  | { type: "refresh" }
  | { type: "ping" }
  | { type: "guide"; node_id: string; command: string; data?: unknown }
  | { type: "set_status"; node_id: string; status: string };
