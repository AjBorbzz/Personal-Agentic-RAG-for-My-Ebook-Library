import { apiGet, apiRequest, type ApiReadOptions } from "./api";

const q = encodeURIComponent;

export type Profile = {
  profile_id: string;
  profile_name: string;
  is_active: boolean;
};

export type Target = {
  career_target_id: string;
  role_name: string;
  status: string;
};

export type Opportunity = {
  skill_id: string;
  skill_name: string;
  gap_type: string;
  gap_steps: number | null;
  career_importance: number | null;
  explanation: string;
  title_suggestion: string;
  source_document_ids: string[];
  source_mapping_ids: string[];
  no_trusted_book_sources: boolean;
};

export type Project = {
  portfolio_project_id: string;
  profile_id: string;
  career_target_id: string;
  title: string;
  slug: string;
  problem_statement: string;
  status: string;
  target_skill_ids: string[];
  source_document_ids: string[];
  source_mapping_ids: string[];
  blueprint_versions: {
    version: number;
    specification: Record<string, unknown>;
    approved: boolean;
  }[];
  approved_blueprint_version: number | null;
  architecture: Record<string, unknown>;
  tech_stack: unknown[];
};

export type Milestone = {
  milestone_id: string;
  title: string;
  description: string;
  sequence_order: number;
  acceptance_criteria: string[];
  completion_notes: string | null;
  status: string;
};

export type Artifact = {
  artifact_id: string;
  title: string;
  content: string;
  artifact_type: string;
  verification_status: string;
  claim_scope: string;
  version: number;
  evidence: Record<string, unknown>;
  file_path: string | null;
  source_url: string | null;
};

export type Readiness = {
  approved_blueprint: boolean;
  milestone_count: number;
  completed_milestones: number;
  verified_artifact_count: number;
  missing: string[];
  publication_ready: boolean;
};

export const portfolioApi = {
  profiles: (options?: ApiReadOptions) =>
    apiGet<Profile[]>("/personal-skill-profiles", options),

  targets: (profile: string, options?: ApiReadOptions) =>
    apiGet<Target[]>(`/career-targets?profile_id=${q(profile)}`, options),

  opportunities: (profile: string, target: string, options?: ApiReadOptions) =>
    apiGet<Opportunity[]>(
      `/portfolio-opportunities?profile_id=${q(profile)}&career_target_id=${q(
        target,
      )}`,
      options,
    ),

  projects: (profile: string, target?: string, options?: ApiReadOptions) =>
    apiGet<Project[]>(
      `/portfolio-projects?profile_id=${q(profile)}${
        target ? `&career_target_id=${q(target)}` : ""
      }`,
      options,
    ),

  project: (id: string, options?: ApiReadOptions) =>
    apiGet<Project>(`/portfolio-projects/${q(id)}`, options),

  create: (body: unknown) =>
    apiRequest<Project>("/portfolio-projects", { method: "POST", json: body }),

  blueprint: (id: string, specification: Record<string, unknown>) =>
    apiRequest<Project>(`/portfolio-projects/${q(id)}/blueprints`, {
      method: "POST",
      json: { specification },
    }),

  approve: (id: string, version: number, review_notes: string) =>
    apiRequest<Project>(`/portfolio-projects/${q(id)}/blueprints/approve`, {
      method: "POST",
      json: { version, review_notes },
    }),

  status: (id: string, status: string) =>
    apiRequest<Project>(`/portfolio-projects/${q(id)}`, {
      method: "PATCH",
      json: { status },
    }),

  milestones: (id: string, options?: ApiReadOptions) =>
    apiGet<Milestone[]>(`/portfolio-projects/${q(id)}/milestones`, options),

  addMilestone: (id: string, body: unknown) =>
    apiRequest<Milestone>(`/portfolio-projects/${q(id)}/milestones`, {
      method: "POST",
      json: body,
    }),

  milestoneStatus: (id: string, status: string, completion_notes: string) =>
    apiRequest<Milestone>(`/portfolio-milestones/${q(id)}`, {
      method: "PATCH",
      json: { status, completion_notes },
    }),

  artifacts: (id: string, options?: ApiReadOptions) =>
    apiGet<Artifact[]>(`/portfolio-projects/${q(id)}/artifacts`, options),

  addArtifact: (id: string, body: unknown) =>
    apiRequest<Artifact>(`/portfolio-projects/${q(id)}/artifacts`, {
      method: "POST",
      json: body,
    }),

  reviewArtifact: (id: string, body: unknown) =>
    apiRequest<Artifact>(`/portfolio-artifacts/${q(id)}/review`, {
      method: "PATCH",
      json: body,
    }),

  draft: (id: string, kind: string) =>
    apiRequest<Artifact>(`/portfolio-projects/${q(id)}/drafts`, {
      method: "POST",
      json: { kind },
    }),

  readiness: (id: string, options?: ApiReadOptions) =>
    apiGet<Readiness>(`/portfolio-projects/${q(id)}/readiness`, options),

  evidenceProposals: (id: string, options?: ApiReadOptions) =>
    apiGet<unknown[]>(
      `/portfolio-projects/${q(id)}/evidence-proposals`,
      options,
    ),
};
