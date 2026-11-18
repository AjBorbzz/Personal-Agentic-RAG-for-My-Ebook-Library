import type {
  CanonicalSkill, CareerTarget, CareerTargetSkill, Evidence, GapResponse,
  Profile, ProficiencyLevel, QueueItem, Recommendation, RecommendationRunDetail,
  SkillState, DecisionStatus, QueueStatus,
} from "./skill-intelligence-types";

const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new Error(`Cannot reach FastAPI at ${BASE}. Check the backend and CORS settings.`);
  }
  if (!response.ok) {
    const raw: unknown = await response.json().catch(() => null);
    const detail = raw && typeof raw === "object" && "detail" in raw
      ? (raw as {detail?: unknown}).detail : raw;
    throw new Error(typeof detail === "string" ? detail :
      detail == null ? `HTTP ${response.status}` : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

const json = (method: "POST" | "PUT" | "PATCH", body: unknown): RequestInit =>
  ({ method, body: JSON.stringify(body) });
const q = (value: string) => encodeURIComponent(value);

export const skillAPI = {
  profiles: () => request<Profile[]>("/personal-skill-profiles"),
  createProfile: (body: { profile_name: string; description?: string; is_default?: boolean }) =>
    request<Profile>("/personal-skill-profiles", json("POST", body)),
  states: (profile: string) =>
    request<SkillState[]>(`/personal-skill-profiles/${q(profile)}/skills`),
  saveState: (profile: string, skill: string, body: Partial<SkillState>) =>
    request<SkillState>(`/personal-skill-profiles/${q(profile)}/skills/${q(skill)}`, json("PUT", body)),
  levels: () => request<ProficiencyLevel[]>("/skill-intelligence/proficiency-levels"),
  // Canonical taxonomy results may be a list or a paginated object depending on current backend.
  // Compare with OpenAPI and adjust this normalization if the installed API differs.
  skills: async (query: string): Promise<CanonicalSkill[]> => {
    const result: unknown = await request<unknown>(`/skill-taxonomy/skills?query=${q(query)}`);
    if (Array.isArray(result)) return result as CanonicalSkill[];
    if (result && typeof result === "object") {
      const rec = result as Record<string, unknown>;
      if (Array.isArray(rec.items)) return rec.items as CanonicalSkill[];
      if (Array.isArray(rec.skills)) return rec.skills as CanonicalSkill[];
    }
    throw new Error("Unexpected taxonomy search response. Compare /skill-taxonomy/skills with OpenAPI.");
  },
  gaps: (profile: string, target?: string) =>
    request<GapResponse>(`/personal-skill-profiles/${q(profile)}/gaps` +
      (target ? `?career_target_id=${q(target)}` : "")),
  targets: (profile: string) => request<CareerTarget[]>(`/career-targets?profile_id=${q(profile)}`),
  target: (profile: string, target: string) => request<CareerTarget>(
    `/career-targets/${q(target)}?profile_id=${q(profile)}`),
  requirements: (profile: string, target: string) => request<CareerTargetSkill[]>(
    `/career-targets/${q(target)}/skills?profile_id=${q(profile)}`),
  createTarget: (body: { profile_id: string; role_name: string; role_slug: string;
      priority: number; status: string; description?: string }) =>
    request<CareerTarget>("/career-targets", json("POST", body)),
  saveRequirement: (target: string, skill: string, body: {
    required_level_id: string; importance_weight: number; is_required: boolean; rationale?: string;
  }) => request<CareerTargetSkill>(`/career-targets/${q(target)}/skills/${q(skill)}`, json("PUT", body)),
  evidence: (profile: string, skill: string) =>
    request<Evidence[]>(`/personal-skill-profiles/${q(profile)}/skills/${q(skill)}/evidence`),
  addEvidence: (profile: string, skill: string, body: {
    evidence_type: string; title: string; description?: string;
  }) => request<Evidence>(`/personal-skill-profiles/${q(profile)}/skills/${q(skill)}/evidence`, json("POST", body)),
  reviewEvidence: (id: string, status: string) =>
    request<Evidence>(`/personal-skill-evidence/${q(id)}`, json("PATCH", {verification_status: status})),
  recommendations: (profile: string, target?: string) =>
    request<Recommendation[]>(`/personal-skill-profiles/${q(profile)}/recommendations` +
      (target ? `?career_target_id=${q(target)}` : "")),
  generate: (profile: string, target?: string) =>
    request<RecommendationRunDetail>("/skill-recommendations/generate", json("POST", {
      profile_id: profile, career_target_id: target ?? null,
    })),
  decide: (id: string, status: DecisionStatus) =>
    request<Recommendation>(`/skill-recommendations/${q(id)}`, json("PATCH", {decision_status: status})),
  enqueue: (profile: string, recommendation: string) =>
    request<QueueItem>("/reading-queue", json("POST", {profile_id: profile,
      recommendation_id: recommendation, priority: 3})),
  queue: (profile: string) => request<QueueItem[]>(`/reading-queue?profile_id=${q(profile)}`),
  updateQueue: (id: string, body: {status?: QueueStatus; progress_percent?: number;
    notes?: string; priority?: number; planned_start?: string | null; target_finish?: string | null}) =>
    request<QueueItem>(`/reading-queue/${q(id)}`, json("PATCH", body)),
};