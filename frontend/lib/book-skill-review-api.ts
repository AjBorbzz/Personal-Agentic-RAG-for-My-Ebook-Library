import { apiGet, apiPatch, type ApiReadOptions } from "./api";
import type {
  BookSkillReview,
  BookSkillReviewQueue,
  BookSkillReviewRequest,
  BookSkillReviewResult,
} from "./book-skill-review-types";

export function fetchBookSkillReviewQueue(
  documentId: string,
  mappingStatus:
    | "pending"
    | "approved"
    | "rejected"
    | "failed"
    | "all" = "pending",
  options?: ApiReadOptions,
): Promise<BookSkillReviewQueue> {
  const parameters = new URLSearchParams({
    mapping_status: mappingStatus === "all" ? "" : mappingStatus,
  });
  const id = encodeURIComponent(documentId);

  return apiGet<BookSkillReviewQueue>(
    `/book-skill-mappings/documents/${id}/review-queue?${parameters}`,
    options,
  );
}

export function fetchBookSkillReview(
  mappingId: string,
  options?: ApiReadOptions,
): Promise<BookSkillReview> {
  return apiGet<BookSkillReview>(
    `/book-skill-mappings/${encodeURIComponent(mappingId)}/review`,
    options,
  );
}

export function submitBookSkillReview(
  mappingId: string,
  request: BookSkillReviewRequest,
): Promise<BookSkillReviewResult> {
  return apiPatch<BookSkillReviewResult, BookSkillReviewRequest>(
    `/book-skill-mappings/${encodeURIComponent(mappingId)}/review`,
    request,
  );
}
