import type {
  BookCuratorDashboard,
  RankingPurpose,
} from "./book-curator-types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface DashboardFilters {
  purpose: RankingPurpose;
  domain?: string;
  topic?: string;
  technology?: string;
  audienceLevel?: string;
}

async function parseApiError(
  response: Response,
): Promise<string> {
  try {
    const body = await response.json();

    if (typeof body.detail === "string") {
      return body.detail;
    }

    return JSON.stringify(body);
  } catch {
    return (
      `Request failed with status ` +
      `${response.status}.`
    );
  }
}

export async function fetchBookCuratorDashboard(
  filters: DashboardFilters,
): Promise<BookCuratorDashboard> {
  const parameters = new URLSearchParams();

  parameters.set(
    "purpose",
    filters.purpose,
  );

  if (filters.domain?.trim()) {
    parameters.set(
      "domain",
      filters.domain.trim(),
    );
  }

  if (filters.topic?.trim()) {
    parameters.set(
      "topic",
      filters.topic.trim(),
    );
  }

  if (filters.technology?.trim()) {
    parameters.set(
      "technology",
      filters.technology.trim(),
    );
  }

  if (filters.audienceLevel?.trim()) {
    parameters.set(
      "audience_level",
      filters.audienceLevel.trim(),
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/book-curator-dashboard?` +
      parameters.toString(),
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await parseApiError(response),
    );
  }

  return response.json();
}

export async function reviewRelationship(
  relationshipId: string,
  action: "approve" | "reject",
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/book-relationships/` +
      `${relationshipId}/review`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await parseApiError(response),
    );
  }
}