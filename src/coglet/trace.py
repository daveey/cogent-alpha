"""CogletTrace — OpenTelemetry-based tracing for coglet event flows.

Pass to CogletRuntime(trace=CogletTrace()) to transparently record
all transmit() and enact() events as OpenTelemetry spans. Supports
OTLP export, console output, and JSONL file recording.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import StatusCode


class _JsonlSpanExporter(SpanExporter):
    """Exports spans as JSONL for backward-compatible file recording."""

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._file = open(self._path, "w")

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            attrs = dict(span.attributes or {})
            # Convert start time from nanoseconds to seconds
            start_ns = span.start_time or 0
            entry = {
                "t": round(start_ns / 1e9, 4),
                "coglet": attrs.get("coglet.type", ""),
                "op": attrs.get("coglet.op", ""),
                "target": attrs.get("coglet.target", ""),
                "span_name": span.name,
                "trace_id": format(span.context.trace_id, "032x"),
                "span_id": format(span.context.span_id, "016x"),
            }
            parent = span.parent
            if parent:
                entry["parent_span_id"] = format(parent.span_id, "016x")
            data = attrs.get("coglet.data")
            if data is not None:
                try:
                    entry["data"] = json.loads(data) if isinstance(data, str) else data
                except (json.JSONDecodeError, TypeError):
                    entry["data"] = data
            self._file.write(json.dumps(entry, default=str) + "\n")
            self._file.flush()
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self._file.close()

    def force_flush(self, timeout_millis: int = 0) -> bool:
        self._file.flush()
        return True


class CogletTrace:
    """OpenTelemetry-based tracer for coglet event flows.

    Usage:
        # JSONL file recording (backward compatible)
        trace = CogletTrace("trace.jsonl")

        # OTLP export to a collector
        trace = CogletTrace(otlp_endpoint="http://localhost:4317")

        # Custom exporter
        trace = CogletTrace(exporter=my_exporter)

        # In-memory (for tests)
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        mem = InMemorySpanExporter()
        trace = CogletTrace(exporter=mem)

        runtime = CogletRuntime(trace=trace)
        # ... run coglets ...
        trace.close()
    """

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        otlp_endpoint: str | None = None,
        exporter: SpanExporter | None = None,
        service_name: str = "coglet",
    ):
        resource = Resource.create({"service.name": service_name})
        self._provider = TracerProvider(resource=resource)

        if exporter is not None:
            self._provider.add_span_processor(SimpleSpanProcessor(exporter))
        elif path is not None:
            self._provider.add_span_processor(
                SimpleSpanProcessor(_JsonlSpanExporter(path))
            )
        elif otlp_endpoint is not None:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            self._provider.add_span_processor(
                SimpleSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
            )

        self._tracer = self._provider.get_tracer("coglet", "0.1.0")

    @property
    def tracer(self) -> trace.Tracer:
        return self._tracer

    @property
    def provider(self) -> TracerProvider:
        return self._provider

    def record(self, coglet_type: str, op: str, target: str, data: Any) -> None:
        """Record a transmit/enact event as an OTel span."""
        with self._tracer.start_as_current_span(
            f"coglet.{op}",
            attributes={
                "coglet.type": coglet_type,
                "coglet.op": op,
                "coglet.target": target,
            },
        ) as span:
            try:
                serialized = json.dumps(data, default=str)
            except (TypeError, ValueError):
                serialized = repr(data)
            span.set_attribute("coglet.data", serialized)

    def close(self) -> None:
        self._provider.shutdown()

    @staticmethod
    def load(path: str | Path) -> list[dict]:
        """Load a JSONL trace file for inspection (backward compatible)."""
        entries = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
