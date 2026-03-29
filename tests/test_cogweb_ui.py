"""Tests for cogweb.ui server — REST API and WebSocket graph endpoint."""
from __future__ import annotations

import json

import pytest

from coglet import Coglet, CogletConfig, CogletRuntime, LifeLet
from coglet.coglet import enact
from coglet.weblet import CogWebRegistry, WebLet
from cogweb.ui.server import CogWebUI, _STATIC_DIR


class WebNode(Coglet, WebLet, LifeLet):
    pass


class GuideableNode(Coglet, WebLet, LifeLet):
    """A coglet that records guide commands for testing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.received_commands: list[tuple[str, object]] = []

    @enact("test_cmd")
    async def handle_test_cmd(self, data):
        self.received_commands.append(("test_cmd", data))

    @enact("reset")
    async def handle_reset(self, data):
        self.received_commands.append(("reset", data))


# --- Static file ---


def test_static_index_exists():
    index = _STATIC_DIR / "index.html"
    assert index.exists()
    content = index.read_text()
    assert "CogWeb" in content


# --- REST API via test client ---


@pytest.fixture
def registry_with_node():
    """Create a registry with one manually registered coglet."""
    reg = CogWebRegistry()
    cog = WebNode(cogweb=reg)
    cog._runtime = None
    reg.register(cog)
    return reg


@pytest.fixture
def app(registry_with_node):
    ui = CogWebUI(registry_with_node)
    return ui._build_app()


def test_api_graph_returns_snapshot(app, registry_with_node):
    from starlette.testclient import TestClient
    client = TestClient(app)
    resp = client.get("/api/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 1
    node = list(data["nodes"].values())[0]
    assert node["class_name"] == "WebNode"


def test_index_serves_html(app):
    from starlette.testclient import TestClient
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "CogWeb" in resp.text


def test_ws_receives_initial_snapshot(app, registry_with_node):
    from starlette.testclient import TestClient
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"
        assert len(msg["data"]["nodes"]) == 1


def test_ws_refresh_command(app, registry_with_node):
    from starlette.testclient import TestClient
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        # Consume initial snapshot
        ws.receive_json()
        # Send refresh
        ws.send_text(json.dumps({"type": "refresh"}))
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"


def test_ws_ping_pong(app):
    from starlette.testclient import TestClient
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # initial snapshot
        ws.send_text(json.dumps({"type": "ping"}))
        msg = ws.receive_json()
        assert msg["type"] == "pong"


def test_ws_invalid_json(app):
    from starlette.testclient import TestClient
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # initial snapshot
        ws.send_text("not json")
        msg = ws.receive_json()
        assert msg["type"] == "error"


# --- Integration with runtime ---


@pytest.mark.asyncio
async def test_runtime_integration():
    """Full pipeline: runtime → WebLet → registry → UI snapshot."""
    reg = CogWebRegistry()
    rt = CogletRuntime()
    handle = await rt.spawn(CogletConfig(cls=WebNode, kwargs={"cogweb": reg}))

    ui = CogWebUI(reg)
    app = ui._build_app()

    from starlette.testclient import TestClient
    client = TestClient(app)
    resp = client.get("/api/graph")
    data = resp.json()
    assert len(data["nodes"]) == 1
    node = list(data["nodes"].values())[0]
    assert node["class_name"] == "WebNode"
    assert node["status"] == "running"

    await rt.shutdown()

    # After shutdown, node is deregistered
    resp = client.get("/api/graph")
    data = resp.json()
    assert len(data["nodes"]) == 0


# --- Control messages (guide, set_status) ---


@pytest.fixture
def guideable_registry():
    """Registry with a GuideableNode that records commands."""
    reg = CogWebRegistry()
    cog = GuideableNode(cogweb=reg)
    cog._runtime = None
    node_id = reg.register(cog)
    return reg, cog, node_id


@pytest.fixture
def guideable_app(guideable_registry):
    reg, _, _ = guideable_registry
    ui = CogWebUI(reg)
    return ui._build_app()


def test_ws_guide_command(guideable_app, guideable_registry):
    """UI can send guide commands to a coglet via WebSocket."""
    _, cog, node_id = guideable_registry
    from starlette.testclient import TestClient
    client = TestClient(guideable_app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # initial snapshot
        ws.send_text(json.dumps({
            "type": "guide",
            "node_id": node_id,
            "command": "test_cmd",
            "data": {"key": "value"},
        }))
        msg = ws.receive_json()
        assert msg["type"] == "guide_result"
        assert msg["ok"] is True
        assert msg["node_id"] == node_id
    # Verify the coglet received the command
    assert len(cog.received_commands) == 1
    assert cog.received_commands[0] == ("test_cmd", {"key": "value"})


def test_ws_guide_unknown_node(guideable_app):
    """Guide to unknown node returns error."""
    from starlette.testclient import TestClient
    client = TestClient(guideable_app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({
            "type": "guide",
            "node_id": "nonexistent_123",
            "command": "test_cmd",
        }))
        msg = ws.receive_json()
        assert msg["type"] == "guide_result"
        assert msg["ok"] is False
        assert "unknown node" in msg["error"]


def test_ws_guide_missing_fields(guideable_app):
    """Guide without required fields returns error."""
    from starlette.testclient import TestClient
    client = TestClient(guideable_app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({"type": "guide", "node_id": "x"}))
        msg = ws.receive_json()
        assert msg["type"] == "guide_result"
        assert msg["ok"] is False


def test_ws_set_status(guideable_app, guideable_registry):
    """UI can change a node's status via WebSocket."""
    reg, _, node_id = guideable_registry
    from starlette.testclient import TestClient
    client = TestClient(guideable_app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({
            "type": "set_status",
            "node_id": node_id,
            "status": "error",
        }))
        msg = ws.receive_json()
        assert msg["type"] == "status_updated"
        assert msg["status"] == "error"
    # Verify status changed in registry
    assert reg._statuses[node_id] == "error"


def test_ws_set_status_unknown_node(guideable_app):
    """set_status for unknown node returns error."""
    from starlette.testclient import TestClient
    client = TestClient(guideable_app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({
            "type": "set_status",
            "node_id": "ghost_456",
            "status": "stopped",
        }))
        msg = ws.receive_json()
        assert msg["type"] == "error"


def test_ws_guide_quick_commands(guideable_app, guideable_registry):
    """Multiple quick commands work sequentially."""
    _, cog, node_id = guideable_registry
    from starlette.testclient import TestClient
    client = TestClient(guideable_app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        # Send two different commands
        ws.send_text(json.dumps({
            "type": "guide", "node_id": node_id,
            "command": "test_cmd", "data": "first",
        }))
        msg1 = ws.receive_json()
        assert msg1["ok"] is True

        ws.send_text(json.dumps({
            "type": "guide", "node_id": node_id,
            "command": "reset", "data": None,
        }))
        msg2 = ws.receive_json()
        assert msg2["ok"] is True

    assert len(cog.received_commands) == 2
    assert cog.received_commands[0] == ("test_cmd", "first")
    assert cog.received_commands[1] == ("reset", None)


def test_dist_index_served_when_built(app):
    """Server serves the Vite dist/index.html when available."""
    from starlette.testclient import TestClient
    from cogweb.ui.server import _DIST_DIR
    dist_index = _DIST_DIR / "index.html"
    if dist_index.exists():
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        # Vite build includes module script
        assert "script" in resp.text.lower()
