import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.book_curations import generate_book_evaluation
from app.core.config import settings
from app.models.book_curation import BookCuration
from app.models.document import Document
from app.schemas.book_evaluation import GenerateBookEvaluationRequest
from app.services.ollama import OllamaOutputLimitError, OllamaStructuredOutputError


class BookCuratorEvaluationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        self.document = Document(document_id="test-ebook", title="API Design")
        self.curation = BookCuration(
            curation_id="test-curation",
            document_id=self.document.document_id,
            evaluation_status="failed",
            evaluation_version=1,
            created_at=now,
            updated_at=now,
        )
        self.db = Mock(spec=Session)
        self.db.get.return_value = self.document
        self.db.scalar.return_value = self.curation
        self.enterContext(
            patch(
                "app.services.book_curator_evaluation.load_document_text",
                return_value="Example ebook content about API design. " * 400,
            )
        )
        self.generate = self.enterContext(
            patch("app.services.book_curator_evaluation.generate_structured_text")
        )

    async def test_generation_bounds_output_and_records_the_curator_model(self):
        self.generate.return_value = json.dumps(
            {
                "technical_depth_score": 75,
                "practicality_score": 75,
                "freshness_score": 75,
                "authority_score": 75,
                "clarity_score": 75,
                "outdated_risk_score": 25,
                "audience_level": "intermediate",
                "recommended_role": "practical_guide",
                "library_priority": "high",
                "curator_summary": "The text explains practical API design.",
            }
        )

        result = await self.evaluate()

        request = self.generate.await_args.kwargs
        self.assertEqual(request["model"], settings.book_curator)
        self.assertFalse(request["think"])
        self.assertEqual(request["max_output_tokens"], 2_048)
        self.assertEqual(request["context_window"], 8_192)
        self.assertEqual(result.evaluation_status, "pending")
        self.assertEqual(result.candidate.overall_score, 75)
        self.assertEqual(result.curation.evaluation_model, settings.book_curator)
        self.assertIsNone(result.curation.overall_score)

    async def test_truncation_retries_once_then_returns_upstream_error(self):
        self.generate.side_effect = OllamaOutputLimitError("Incomplete JSON")

        with self.assertRaises(HTTPException) as caught:
            await self.evaluate()

        self.assertEqual(caught.exception.status_code, 502)
        self.assertEqual(self.generate.await_count, 2)
        first, second = self.generate.await_args_list
        self.assertLess(len(second.kwargs["prompt"]), len(first.kwargs["prompt"]))
        self.assertEqual(self.curation.evaluation_status, "failed")
        self.assertIsNone(self.curation.evaluation_candidate)

    async def test_timeout_suggests_waiting_for_other_requests(self):
        self.generate.side_effect = TimeoutError()

        with self.assertRaises(HTTPException) as caught:
            await self.evaluate()

        self.assertEqual(caught.exception.status_code, 504)
        self.assertIn("another AI request", caught.exception.detail)
        self.assertEqual(self.curation.evaluation_error, caught.exception.detail)
        self.generate.assert_awaited_once()

    async def test_upstream_failure_is_not_retried_or_reported_as_timeout(self):
        self.generate.side_effect = OllamaStructuredOutputError("Cannot connect")

        with self.assertRaises(HTTPException) as caught:
            await self.evaluate()

        self.assertEqual(caught.exception.status_code, 502)
        self.assertEqual(self.curation.evaluation_status, "failed")
        self.generate.assert_awaited_once()

    async def evaluate(self):
        return await generate_book_evaluation(
            self.document.document_id, GenerateBookEvaluationRequest(), self.db
        )
