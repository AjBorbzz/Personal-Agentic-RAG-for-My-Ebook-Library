import type {
  BookSkillReview,
  BookSkillReviewQueue,
  BookSkillReviewRequest,
  BookSkillReviewResult,
} from "./book-skill-review-types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

async function apiError(
  response: Response,
): Promise<string> {
  try {
    const body: unknown =
      await response.json();

    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body
    ) {
      const detail = (
        body as {
          detail?: unknown;
        }
      ).detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (detail !== undefined) {
        return JSON.stringify(detail);
      }
    }

    return JSON.stringify(body);
  } catch {
    return (
      `Request failed with status ` +
      `${response.status}.`
    );
  }
}

export async function fetchBookSkillReviewQueue(
  documentId: string,
  mappingStatus:
    | "pending"
    | "approved"
    | "rejected"
    | "failed"
    | "all" = "pending",
): Promise<BookSkillReviewQueue> {
  const parameters =
    new URLSearchParams();

  parameters.set(
    "mapping_status",
    mappingStatus === "all"
      ? ""
      : mappingStatus,
  );

  const response = await fetch(
    `${API_BASE_URL}/book-skill-mappings/` +
      `documents/${documentId}/review-queue?` +
      parameters.toString(),
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await apiError(response),
    );
  }

  return response.json();
}

export async function fetchBookSkillReview(
  mappingId: string,
): Promise<BookSkillReview> {
  const response = await fetch(
    `${API_BASE_URL}/book-skill-mappings/` +
      `${mappingId}/review`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await apiError(response),
    );
  }

  return response.json();
}

export async function submitBookSkillReview(
  mappingId: string,
  request: BookSkillReviewRequest,
): Promise<BookSkillReviewResult> {
  const response = await fetch(
    `${API_BASE_URL}/book-skill-mappings/` +
      `${mappingId}/review`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw new Error(
      await apiError(response),
    );
  }

  return response.json();
}