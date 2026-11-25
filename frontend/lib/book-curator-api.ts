import { apiGet, apiRequest, type ApiReadOptions } from "./api";
import type {
  BookCuratorDashboard,
  RankingPurpose,
} from "./book-curator-types";

export interface DashboardFilters {
  purpose: RankingPurpose;
  domain?: string;
  topic?: string;
  technology?: string;
  audienceLevel?: string;
}

export function fetchBookCuratorDashboard(
  filters: DashboardFilters,
  options?: ApiReadOptions,
): Promise<BookCuratorDashboard> {
  const parameters = new URLSearchParams({ purpose: filters.purpose });
  const optionalFilters = {
    domain: filters.domain,
    topic: filters.topic,
    technology: filters.technology,
    audience_level: filters.audienceLevel,
  };

  for (const [key, value] of Object.entries(optionalFilters)) {
    const trimmed = value?.trim();
    if (trimmed) parameters.set(key, trimmed);
  }

  return apiGet<BookCuratorDashboard>(
    `/book-curator-dashboard?${parameters}`,
    options,
  );
}

export function reviewRelationship(
  relationshipId: string,
  action: "approve" | "reject",
): Promise<void> {
  return apiRequest(
    `/book-relationships/${encodeURIComponent(relationshipId)}/review`,
    {
      method: "PATCH",
      json: { action },
      responseType: "void",
    },
  );
}
