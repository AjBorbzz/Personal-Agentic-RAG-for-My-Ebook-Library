import { apiGet, type ApiReadOptions } from "./api";
import type {
  SkillDetail,
  SkillSearchResponse,
  SkillTaxonomyTree,
} from "./skill-taxonomy-types";

export function fetchSkillTree(
  options?: ApiReadOptions,
): Promise<SkillTaxonomyTree> {
  return apiGet<SkillTaxonomyTree>("/skill-taxonomy/tree", options);
}

export function searchSkills(
  query: string,
  options?: ApiReadOptions,
): Promise<SkillSearchResponse> {
  const parameters = new URLSearchParams();
  const trimmed = query.trim();
  if (trimmed) parameters.set("query", trimmed);
  parameters.set("limit", "100");

  return apiGet<SkillSearchResponse>(
    `/skill-taxonomy/skills?${parameters}`,
    options,
  );
}

export function fetchSkillDetail(
  skillId: string,
  options?: ApiReadOptions,
): Promise<SkillDetail> {
  return apiGet<SkillDetail>(
    `/skill-taxonomy/skills/${encodeURIComponent(skillId)}`,
    options,
  );
}
