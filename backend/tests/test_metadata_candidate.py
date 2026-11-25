import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.documents import stage_metadata_candidate
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.schemas.metadata_review import StageMetadataCandidateRequest
from app.services.book_metadata_enrichment import generate_metadata_candidate


class MetadataCandidateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        fields = dict.fromkeys(DocumentResponse.model_fields)
        fields.update(
            document_id="test-ebook",
            filename="test-ebook.txt",
            is_active=True,
            is_deprecated=False,
            ingested_at=now,
            created_at=now,
            updated_at=now,
            metadata_reviewed=False,
            metadata_review_status="not_requested",
        )
        self.document = Document(**fields)
        self.db = Mock(spec=Session)
        self.db.get.return_value = self.document
        self.payloads = []
        self.enterContext(
            patch(
                "app.services.book_metadata_enrichment.load_document_text",
                return_value="A technical ebook about API design. " * 2000,
            )
        )

    def mock_ollama(self, *bodies):
        responses = iter(bodies)
        client_type = httpx.AsyncClient

        def generate(request):
            self.payloads.append(json.loads(request.content))
            return httpx.Response(200, json=next(responses))

        return patch(
            "app.services.ollama.httpx.AsyncClient",
            side_effect=lambda **options: client_type(
                transport=httpx.MockTransport(generate), **options
            ),
        )

    async def test_metadata_reserves_room_for_json_without_thinking(self):
        with self.mock_ollama(
            {"done_reason": "length", "response": '{"title":"API Design"}'}
        ):
            candidate, _, _ = await generate_metadata_candidate(self.document, 24_000)

        self.assertEqual(candidate.title, "API Design")
        self.assertEqual(len(self.payloads), 1)
        self.assertIs(self.payloads[0]["think"], False)
        self.assertEqual(self.payloads[0]["options"]["num_ctx"], 16_384)
        self.assertEqual(self.payloads[0]["options"]["num_predict"], 4_096)

    async def test_length_stop_retries_with_less_source_and_stages_candidate(self):
        with self.mock_ollama(
            {"done_reason": "length", "response": "", "thinking": "Some reasoning"},
            {"done_reason": "stop", "response": '{"title":"API Design"}'},
        ):
            result = await stage_metadata_candidate(
                self.document.document_id, StageMetadataCandidateRequest(), self.db
            )

        self.assertEqual(result.review_status, "pending")
        self.assertEqual(result.candidate.title, "API Design")
        self.assertIsNone(self.document.title)
        self.assertTrue(result.source_was_truncated)
        self.assertLess(result.source_characters_used, 24_000)
        self.assertEqual(len(self.payloads), 2)
        self.assertLess(
            len(self.payloads[1]["prompt"]), len(self.payloads[0]["prompt"])
        )
        self.db.commit.assert_called_once()

    async def test_second_length_stop_returns_actionable_error_without_staging(self):
        length_stop = {"done_reason": "length", "response": '{"title":'}
        with (
            self.mock_ollama(length_stop, length_stop),
            self.assertRaises(HTTPException) as caught,
        ):
            await stage_metadata_candidate(
                self.document.document_id, StageMetadataCandidateRequest(), self.db
            )

        self.assertEqual(caught.exception.status_code, 502)
        self.assertIn("smaller source character limit", caught.exception.detail)
        self.assertEqual(len(self.payloads), 2)
        self.assertEqual(self.document.metadata_review_status, "not_requested")
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()
