"""Unit tests for coglet.trace: OpenTelemetry-based CogletTrace."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from coglet.trace import CogletTrace


def test_trace_record_and_load():
    """CogletTrace records events and JSONL load works."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        trace = CogletTrace(path)
        trace.record("TestCoglet", "transmit", "ch1", {"key": "value"})
        trace.record("TestCoglet", "enact", "cmd1", "data")
        trace.close()

        entries = CogletTrace.load(path)
        assert len(entries) == 2
        assert entries[0]["coglet"] == "TestCoglet"
        assert entries[0]["op"] == "transmit"
        assert entries[0]["target"] == "ch1"
        assert entries[0]["data"] == {"key": "value"}
        assert entries[1]["op"] == "enact"
    finally:
        Path(path).unlink(missing_ok=True)


def test_trace_has_otel_fields():
    """JSONL entries include trace_id and span_id."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        trace = CogletTrace(path)
        trace.record("A", "transmit", "ch", 1)
        trace.close()

        entries = CogletTrace.load(path)
        assert "trace_id" in entries[0]
        assert "span_id" in entries[0]
        assert len(entries[0]["trace_id"]) == 32  # 128-bit hex
        assert len(entries[0]["span_id"]) == 16   # 64-bit hex
    finally:
        Path(path).unlink(missing_ok=True)


def test_trace_in_memory_exporter():
    """InMemorySpanExporter captures spans for test inspection."""
    mem = InMemorySpanExporter()
    trace = CogletTrace(exporter=mem)
    trace.record("TestCoglet", "transmit", "ch1", {"key": "value"})
    trace.record("TestCoglet", "enact", "cmd1", "data")
    trace.close()

    spans = mem.get_finished_spans()
    assert len(spans) == 2
    assert spans[0].name == "coglet.transmit"
    assert spans[0].attributes["coglet.type"] == "TestCoglet"
    assert spans[0].attributes["coglet.target"] == "ch1"
    assert spans[1].name == "coglet.enact"
    assert spans[1].attributes["coglet.target"] == "cmd1"


def test_trace_unserializable_data():
    """Non-JSON-serializable data is repr'd instead of crashing."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        trace = CogletTrace(path)
        trace.record("A", "transmit", "ch", object())
        trace.close()

        entries = CogletTrace.load(path)
        assert len(entries) == 1
        assert isinstance(entries[0]["data"], str)
    finally:
        Path(path).unlink(missing_ok=True)


def test_trace_load_empty():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        trace = CogletTrace(path)
        trace.close()
        entries = CogletTrace.load(path)
        assert entries == []
    finally:
        Path(path).unlink(missing_ok=True)


def test_trace_span_names():
    """Span names follow coglet.{op} convention."""
    mem = InMemorySpanExporter()
    trace = CogletTrace(exporter=mem)
    trace.record("Cog", "transmit", "out", "x")
    trace.record("Cog", "enact", "cmd", "y")
    trace.close()

    names = [s.name for s in mem.get_finished_spans()]
    assert names == ["coglet.transmit", "coglet.enact"]
