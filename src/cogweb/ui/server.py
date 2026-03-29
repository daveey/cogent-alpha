"""CogWeb UI server — Starlette + WebSocket bridge to CogWebRegistry.

Serves the React Flow graph editor (Vite build output) and provides:
  GET  /           — single-page app (React Flow graph editor)
  GET  /api/graph  — JSON snapshot of the current graph
  WS   /ws         — live graph updates + control commands from browser
"""
from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
from pathlib import Path
from typing import Any

from coglet.handle import Command
from coglet.weblet import CogWebRegistry

logger = logging.getLogger("cogweb.ui")

# Vite builds into static/dist/; fall back to static/ for legacy index.html
_STATIC_DIR = Path(__file__).parent / "static"
_DIST_DIR = _STATIC_DIR / "dist"


class CogWebUI:
    """Wraps a CogWebRegistry with an HTTP/WebSocket server.

    Usage:
        from coglet.weblet import CogWebRegistry
        from cogweb.ui import CogWebUI

        registry = CogWebRegistry()
        ui = CogWebUI(registry, host="0.0.0.0", port=8787)
        await ui.start()   # non-blocking, runs in background
        ...
        await ui.stop()
    """

    def __init__(
        self,
        registry: CogWebRegistry,
        host: str = "127.0.0.1",
        port: int = 8787,
        poll_interval: float = 0.5,
    ):
        self.registry = registry
        self.host = host
        self.port = port
        self.poll_interval = poll_interval
        self._app: Any = None
        self._server_task: asyncio.Task[None] | None = None
        self._ws_clients: list[Any] = []

    def _build_app(self) -> Any:
        """Build the Starlette/ASGI app (avoids import at module level)."""
        from starlette.applications import Starlette
        from starlette.responses import HTMLResponse, JSONResponse
        from starlette.routing import Route, WebSocketRoute
        from starlette.websockets import WebSocket

        registry = self.registry
        ws_clients = self._ws_clients

        def _resolve_index() -> Path:
            """Find the SPA index.html — prefer Vite dist, fall back to legacy."""
            dist_index = _DIST_DIR / "index.html"
            if dist_index.exists():
                return dist_index
            return _STATIC_DIR / "index.html"

        async def index(request: Any) -> HTMLResponse:
            return HTMLResponse(_resolve_index().read_text())

        async def api_graph(request: Any) -> JSONResponse:
            snap = registry.snapshot()
            return JSONResponse(snap.to_dict())

        async def ws_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            ws_clients.append(websocket)
            try:
                # Send initial snapshot
                snap = registry.snapshot()
                await websocket.send_json({"type": "snapshot", "data": snap.to_dict()})
                # Keep connection alive — client may send commands
                while True:
                    raw = await websocket.receive_text()
                    try:
                        msg = json.loads(raw)
                        await self._handle_ws_message(websocket, msg)
                    except json.JSONDecodeError:
                        await websocket.send_json({"type": "error", "data": "invalid json"})
            except Exception:
                pass
            finally:
                if websocket in ws_clients:
                    ws_clients.remove(websocket)

        async def _serve_file(file_path: Path) -> Any:
            """Serve a static file with correct MIME type."""
            from starlette.responses import Response
            mime, _ = mimetypes.guess_type(file_path.name)
            if mime is None:
                mime = "application/octet-stream"
            return Response(file_path.read_bytes(), media_type=mime)

        async def assets(request: Any) -> Any:
            """Serve Vite build assets (JS/CSS chunks in dist/assets/)."""
            filename = request.path_params.get("path", "")
            file_path = _DIST_DIR / "assets" / filename
            if file_path.exists() and file_path.is_file():
                return await _serve_file(file_path)
            return HTMLResponse("Not found", status_code=404)

        async def static_file(request: Any) -> Any:
            """Serve files from static/ or dist/ directories."""
            filename = request.path_params.get("path", "")
            # Try dist/ first, then static/
            for base in (_DIST_DIR, _STATIC_DIR):
                file_path = base / filename
                if file_path.exists() and file_path.is_file():
                    return await _serve_file(file_path)
            return HTMLResponse("Not found", status_code=404)

        async def spa_fallback(request: Any) -> HTMLResponse:
            """SPA fallback — serve index.html for unmatched routes."""
            return HTMLResponse(_resolve_index().read_text())

        app = Starlette(
            routes=[
                Route("/", index),
                Route("/api/graph", api_graph),
                Route("/assets/{path:path}", assets),
                Route("/static/{path:path}", static_file),
                WebSocketRoute("/ws", ws_endpoint),
                Route("/{path:path}", spa_fallback),
            ],
        )
        return app

    async def _handle_ws_message(self, websocket: Any, msg: dict) -> None:
        """Handle incoming WebSocket messages from the UI."""
        msg_type = msg.get("type")
        if msg_type == "refresh":
            snap = self.registry.snapshot()
            await websocket.send_json({"type": "snapshot", "data": snap.to_dict()})

        elif msg_type == "ping":
            await websocket.send_json({"type": "pong"})

        elif msg_type == "guide":
            # Send a Command to a coglet: {type: "guide", node_id, command, data}
            node_id = msg.get("node_id")
            command_type = msg.get("command")
            command_data = msg.get("data")
            result = await self._dispatch_guide(node_id, command_type, command_data)
            await websocket.send_json({"type": "guide_result", "node_id": node_id, **result})

        elif msg_type == "set_status":
            # Set node status: {type: "set_status", node_id, status}
            node_id = msg.get("node_id")
            status = msg.get("status", "running")
            if node_id and node_id in self.registry._statuses:
                self.registry.set_status(node_id, status)
                await websocket.send_json({"type": "status_updated", "node_id": node_id, "status": status})
            else:
                await websocket.send_json({"type": "error", "data": f"unknown node: {node_id}"})

    async def _dispatch_guide(self, node_id: str | None, command_type: str | None,
                              command_data: Any) -> dict[str, Any]:
        """Send a guide command to a coglet via its handle."""
        if not node_id or not command_type:
            return {"ok": False, "error": "node_id and command required"}

        coglet = self.registry._coglets.get(node_id)
        if coglet is None:
            return {"ok": False, "error": f"unknown node: {node_id}"}

        try:
            cmd = Command(type=command_type, data=command_data)
            await coglet._dispatch_enact(cmd)
            return {"ok": True}
        except Exception as e:
            logger.warning("guide command failed for %s: %s", node_id, e)
            return {"ok": False, "error": str(e)}

    async def _broadcast_loop(self) -> None:
        """Periodically push graph snapshots to all connected WebSocket clients."""
        last_snapshot: str = ""
        while True:
            await asyncio.sleep(self.poll_interval)
            if not self._ws_clients:
                continue
            snap = self.registry.snapshot()
            snap_json = json.dumps(snap.to_dict(), default=str)
            if snap_json == last_snapshot:
                continue
            last_snapshot = snap_json
            msg = {"type": "snapshot", "data": snap.to_dict()}
            dead: list[Any] = []
            for ws in self._ws_clients:
                try:
                    await ws.send_json(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._ws_clients.remove(ws)

    async def start(self) -> None:
        """Start the UI server in the background."""
        import uvicorn

        self._app = self._build_app()
        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)

        self._server_task = asyncio.create_task(server.serve())
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info(f"CogWeb UI running at http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the UI server."""
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        if hasattr(self, "_broadcast_task") and self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        # Close all WebSocket connections
        for ws in self._ws_clients:
            try:
                await ws.close()
            except Exception:
                pass
        self._ws_clients.clear()
