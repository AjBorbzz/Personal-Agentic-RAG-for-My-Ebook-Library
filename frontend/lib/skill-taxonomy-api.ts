import type {
  SkillDetail,
  SkillSearchResponse,
  SkillTaxonomyTree,
} from "./skill-taxonomy-types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

async function apiError(
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

export async function fetchSkillTree():
Promise<SkillTaxonomyTree> {
  const response = await fetch(
    `${API_BASE_URL}/skill-taxonomy/tree`,
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

export async function searchSkills(
  query: string,
): Promise<SkillSearchResponse> {
  const parameters = new URLSearchParams();

  if (query.trim()) {
    parameters.set(
      "query",
      query.trim(),
    );
  }

  parameters.set("limit", "100");

  const response = await fetch(
    `${API_BASE_URL}/skill-taxonomy/skills?` +
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

export async function fetchSkillDetail(
  skillId: string,
): Promise<SkillDetail> {
  const response = await fetch(
    `${API_BASE_URL}/skill-taxonomy/skills/` +
      skillId,
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