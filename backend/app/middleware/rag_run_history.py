"""ASGI observation only: no changes to retrieval, prompting, responses or filters."""
from __future__ import annotations
import json
import logging
import time

from app.db.session import SessionLocal
from app.models.evaluation import RagRunHistory
from app.evaluation.metrics import sources_from_payload, normalize_source

log = logging.getLogger(__name__)
_REQUEST_LIMIT = 65536
_RESPONSE_LIMIT = 524288


class RagRunHistoryMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if path != "/rag-chat" and "agentic-rag" not in path:
            return await self.app(scope, receive, send)
        request_buf = bytearray()
        response_buf = bytearray()
        status_code = 500
        started = time.monotonic()
        raised = None

        async def receive_capture():
            msg = await receive()
            if msg["type"] == "http.request":
                chunk = msg.get("body", b"")
                available = _REQUEST_LIMIT - len(request_buf)
                if available > 0:
                    request_buf.extend(chunk[:available])
            return msg

        async def send_capture(msg):
            nonlocal status_code
            if msg["type"] == "http.response.start":
                status_code = msg["status"]
            elif msg["type"] == "http.response.body":
                chunk = msg.get("body", b"")
                available = _RESPONSE_LIMIT - len(response_buf)
                if available > 0:
                    response_buf.extend(chunk[:available])
            await send(msg)

        try:
            await self.app(scope, receive_capture, send_capture)
        except Exception as exc:
            raised = type(exc).__name__
            raise
        finally:
            def parse(raw):
                try:
                    value = json.loads(bytes(raw))
                    return value if isinstance(value, dict) else {}
                except (ValueError, UnicodeDecodeError):
                    return {}
            request = parse(request_buf)
            response = parse(response_buf)
            try:
                raw_sources = sources_from_payload(response)
            except ValueError:
                raw_sources = []
            sources = [normalize_source(x) for x in raw_sources]
            # Copy only recognized, bounded metadata. Ebook chunk text and secrets
            # are not written into the trace.
            request_metadata = {k: request[k] for k in (
                "limit", "active_only", "include_deprecated", "domains",
                "tool_name", "tool_version", "source_type", "publication_year"
            ) if k in request}
            raw_attempts = response.get("attempts") if isinstance(response.get("attempts"), list) else []
            attempts = [
                {key: str(item[key])[:200] for key in ("strategy", "route", "status", "source_count") if key in item}
                for item in raw_attempts[:20] if isinstance(item, dict)
            ]
            rewrites = response.get("rewritten_queries") if isinstance(response.get("rewritten_queries"), list) else []
            rewrites = [str(q)[:300] for q in rewrites[:20]]
            try:
                with SessionLocal() as db:
                    db.add(RagRunHistory(
                        request_type="agentic_rag" if "agentic" in path else "basic_rag",
                        question=str(request.get("question") or request.get("query") or "")[:3000],
                        request_payload=request_metadata,
                        intent=str(response.get("intent"))[:120] if response.get("intent") else None,
                        strategy=str(response.get("strategy"))[:120] if response.get("strategy") else None,
                        domains=response.get("domains") if isinstance(response.get("domains"), list) else [],
                        rewritten_queries=rewrites,
                        attempts=attempts,
                        retrieved_sources=sources[:50],
                        answer=str(response.get("answer") or "")[:10000],
                        citations=sources[:50],
                        fallback_used=(bool(response["fallback_used"]) if response.get("fallback_used") is not None else None),
                        weak_source=(bool(response["weak_source"]) if response.get("weak_source") is not None else None),
                        status_code=status_code,
                        latency_ms=int((time.monotonic() - started) * 1000),
                        error_detail=raised or (f"HTTP {status_code}" if status_code >= 400 else None),
                    ))
                    db.commit()
            except Exception:
                log.warning("Phase 14 RAG trace write failed", exc_info=True)