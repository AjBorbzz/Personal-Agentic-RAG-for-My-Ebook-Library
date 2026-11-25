import { apiGet, apiRequest, type ApiReadOptions } from "./api";
import type {
  CanonicalSkill,
  CareerTarget,
  CareerTargetSkill,
  DecisionStatus,
  Evidence,
  GapResponse,
  Profile,
  ProficiencyLevel,
  QueueItem,
  QueueStatus,
  Recommendation,
  RecommendationRunDetail,
  SkillState,
} from "./skill-intelligence-types";

const q = encodeURIComponent;

export const skillAPI = {
  profiles: (options?: ApiReadOptions) =>
    apiGet<Profile[]>("/personal-skill-profiles", options),

  createProfile: (body: {
    profile_name: string;
    description?: string;
    is_default?: boolean;
  }) =>
    apiRequest<Profile>("/personal-skill-profiles", {
      method: "POST",
      json: body,
    }),

  states: (profile: string, options?: ApiReadOptions) =>
    apiGet<SkillState[]>(
      `/personal-skill-profiles/${q(profile)}/skills`,
      options,
    ),

  saveState: (profile: string, skill: string, body: Partial<SkillState>) =>
    apiRequest<SkillState>(
      `/personal-skill-profiles/${q(profile)}/skills/${q(skill)}`,
      {
        method: "PUT",
        json: body,
      },
    ),

  levels: (options?: ApiReadOptions) =>
    apiGet<ProficiencyLevel[]>(
      "/skill-intelligence/proficiency-levels",
      options,
    ),

  skills: async (
    query: string,
    options?: ApiReadOptions,
  ): Promise<CanonicalSkill[]> => {
    const result = await apiGet<unknown>(
      `/skill-taxonomy/skills?query=${q(query)}`,
      options,
    );
    if (Array.isArray(result)) return result as CanonicalSkill[];

    if (result && typeof result === "object") {
      if ("items" in result && Array.isArray(result.items))
        return result.items as CanonicalSkill[];
      if ("skills" in result && Array.isArray(result.skills))
        return result.skills as CanonicalSkill[];
    }

    throw new Error(
      "The backend returned an unexpected taxonomy search response.",
    );
  },

  gaps: (profile: string, target?: string, options?: ApiReadOptions) =>
    apiGet<GapResponse>(
      `/personal-skill-profiles/${q(profile)}/gaps` +
        (target ? `?career_target_id=${q(target)}` : ""),
      options,
    ),

  targets: (profile: string, options?: ApiReadOptions) =>
    apiGet<CareerTarget[]>(`/career-targets?profile_id=${q(profile)}`, options),

  target: (profile: string, target: string, options?: ApiReadOptions) =>
    apiGet<CareerTarget>(
      `/career-targets/${q(target)}?profile_id=${q(profile)}`,
      options,
    ),

  requirements: (profile: string, target: string, options?: ApiReadOptions) =>
    apiGet<CareerTargetSkill[]>(
      `/career-targets/${q(target)}/skills?profile_id=${q(profile)}`,
      options,
    ),

  createTarget: (body: {
    profile_id: string;
    role_name: string;
    role_slug: string;
    priority: number;
    status: string;
    description?: string;
  }) =>
    apiRequest<CareerTarget>("/career-targets", { method: "POST", json: body }),

  saveRequirement: (
    target: string,
    skill: string,
    body: {
      required_level_id: string;
      importance_weight: number;
      is_required: boolean;
      rationale?: string;
    },
  ) =>
    apiRequest<CareerTargetSkill>(
      `/career-targets/${q(target)}/skills/${q(skill)}`,
      {
        method: "PUT",
        json: body,
      },
    ),

  evidence: (profile: string, skill: string, options?: ApiReadOptions) =>
    apiGet<Evidence[]>(
      `/personal-skill-profiles/${q(profile)}/skills/${q(skill)}/evidence`,
      options,
    ),

  addEvidence: (
    profile: string,
    skill: string,
    body: {
      evidence_type: string;
      title: string;
      description?: string;
    },
  ) =>
    apiRequest<Evidence>(
      `/personal-skill-profiles/${q(profile)}/skills/${q(skill)}/evidence`,
      {
        method: "POST",
        json: body,
      },
    ),

  reviewEvidence: (id: string, status: string) =>
    apiRequest<Evidence>(`/personal-skill-evidence/${q(id)}`, {
      method: "PATCH",
      json: { verification_status: status },
    }),

  recommendations: (
    profile: string,
    target?: string,
    options?: ApiReadOptions,
  ) =>
    apiGet<Recommendation[]>(
      `/personal-skill-profiles/${q(profile)}/recommendations` +
        (target ? `?career_target_id=${q(target)}` : ""),
      options,
    ),

  generate: (profile: string, target?: string) =>
    apiRequest<RecommendationRunDetail>("/skill-recommendations/generate", {
      method: "POST",
      json: { profile_id: profile, career_target_id: target ?? null },
    }),

  decide: (id: string, status: DecisionStatus) =>
    apiRequest<Recommendation>(`/skill-recommendations/${q(id)}`, {
      method: "PATCH",
      json: { decision_status: status },
    }),

  enqueue: (profile: string, recommendation: string) =>
    apiRequest<QueueItem>("/reading-queue", {
      method: "POST",
      json: {
        profile_id: profile,
        recommendation_id: recommendation,
        priority: 3,
      },
    }),

  queue: (profile: string, options?: ApiReadOptions) =>
    apiGet<QueueItem[]>(`/reading-queue?profile_id=${q(profile)}`, options),

  updateQueue: (
    id: string,
    body: {
      status?: QueueStatus;
      progress_percent?: number;
      notes?: string;
      priority?: number;
      planned_start?: string | null;
      target_finish?: string | null;
    },
  ) =>
    apiRequest<QueueItem>(`/reading-queue/${q(id)}`, {
      method: "PATCH",
      json: body,
    }),
};
