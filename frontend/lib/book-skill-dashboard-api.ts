import { apiGet, type ApiReadOptions } from "./api";
import type { BookSkillDashboard } from "./book-skill-dashboard-types";

export function fetchBookSkillDashboard(
  domainSlug?: string,
  limit = 10,
  options?: ApiReadOptions,
): Promise<BookSkillDashboard> {
  const parameters = new URLSearchParams();
  if (domainSlug) parameters.set("domain_slug", domainSlug);
  parameters.set("limit", String(limit));

  return apiGet<BookSkillDashboard>(
    `/book-skill-dashboard?${parameters}`,
    options,
  );
}
