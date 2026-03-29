import { useCallback, useEffect, useRef, useState } from "react";
import type { CogWebSnapshot, WSIncoming, WSOutgoing } from "./types";

const RECONNECT_MS = 2000;
const PING_MS = 15000;

export function useWebSocket(onSnapshot: (snap: CogWebSnapshot) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval>>();

  const connect = useCallback(() => {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${location.host}/ws`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      wsRef.current = ws;
      setConnected(true);
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, PING_MS);
    };

    ws.onmessage = (event) => {
      const msg: WSIncoming = JSON.parse(event.data);
      if (msg.type === "snapshot") {
        onSnapshot(msg.data);
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
      setConnected(false);
      clearInterval(pingRef.current);
      setTimeout(connect, RECONNECT_MS);
    };

    ws.onerror = () => ws.close();
  }, [onSnapshot]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      clearInterval(pingRef.current);
    };
  }, [connect]);

  const send = useCallback((msg: WSOutgoing) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  return { connected, send };
}
