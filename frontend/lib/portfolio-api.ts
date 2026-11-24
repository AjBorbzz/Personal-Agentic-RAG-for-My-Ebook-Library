// Phase 15 only: typed client for the new FastAPI portfolio router.
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const q = encodeURIComponent;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { cache: "no-store", ...init });
  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body === "object" && body !== null && "detail" in body
      ? JSON.stringify((body as { detail: unknown }).detail) : response.statusText;
    throw new Error(`${response.status}: ${detail}`);
  }
  return body as T;
}
const json = (method: string, data: unknown): RequestInit => ({
  method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
});

export type Profile = { profile_id: string; profile_name: string; is_active: boolean };
export type Target = { career_target_id: string; role_name: string; status: string };
export type Opportunity = {
  skill_id: string; skill_name: string; gap_type: string; gap_steps: number | null;
  career_importance: number | null; explanation: string; title_suggestion: string;
  source_document_ids: string[]; source_mapping_ids: string[]; no_trusted_book_sources: boolean;
};
export type Project = {
  portfolio_project_id: string; profile_id: string; career_target_id: string;
  title: string; slug: string; problem_statement: string; status: string;
  target_skill_ids: string[]; source_document_ids: string[]; source_mapping_ids: string[];
  blueprint_versions: { version: number; specification: Record<string, unknown>; approved: boolean }[];
  approved_blueprint_version: number | null;
  architecture: Record<string, unknown>; tech_stack: unknown[];
};
export type Milestone = {
  milestone_id: string; title: string; description: string; sequence_order: number;
  acceptance_criteria: string[]; completion_notes: string | null; status: string;
};
export type Artifact = {
  artifact_id: string; title: string; content: string; artifact_type: string;
  verification_status: string; claim_scope: string; version: number;
  evidence: Record<string, unknown>; file_path: string | null; source_url: string | null;
};
export type Readiness = {
  approved_blueprint: boolean; milestone_count: number; completed_milestones: number;
  verified_artifact_count: number; missing: string[]; publication_ready: boolean;
};

export const portfolioApi = {
  profiles: () => request<Profile[]>("/personal-skill-profiles"),
  targets: (profile: string) => request<Target[]>(`/career-targets?profile_id=${q(profile)}`),
  opportunities: (profile: string, target: string) =>
    request<Opportunity[]>(`/portfolio-opportunities?profile_id=${q(profile)}&career_target_id=${q(target)}`),
  projects: (profile: string, target?: string) => request<Project[]>(
    `/portfolio-projects?profile_id=${q(profile)}${target ? `&career_target_id=${q(target)}` : ""}`),
  project: (id: string) => request<Project>(`/portfolio-projects/${q(id)}`),
  create: (body: unknown) => request<Project>("/portfolio-projects", json("POST", body)),
  blueprint: (id: string, specification: Record<string, unknown>) =>
    request<Project>(`/portfolio-projects/${q(id)}/blueprints`, json("POST", { specification })),
  approve: (id: string, version: number, review_notes: string) =>
    request<Project>(`/portfolio-projects/${q(id)}/blueprints/approve`, json("POST", { version, review_notes })),
  status: (id: string, status: string) =>
    request<Project>(`/portfolio-projects/${q(id)}`, json("PATCH", { status })),
  milestones: (id: string) => request<Milestone[]>(`/portfolio-projects/${q(id)}/milestones`),
  addMilestone: (id: string, body: unknown) =>
    request<Milestone>(`/portfolio-projects/${q(id)}/milestones`, json("POST", body)),
  milestoneStatus: (id: string, status: string, completion_notes: string) =>
    request<Milestone>(`/portfolio-milestones/${q(id)}`, json("PATCH", { status, completion_notes })),
  artifacts: (id: string) => request<Artifact[]>(`/portfolio-projects/${q(id)}/artifacts`),
  addArtifact: (id: string, body: unknown) =>
    request<Artifact>(`/portfolio-projects/${q(id)}/artifacts`, json("POST", body)),
  reviewArtifact: (id: string, body: unknown) =>
    request<Artifact>(`/portfolio-artifacts/${q(id)}/review`, json("PATCH", body)),
  draft: (id: string, kind: string) =>
    request<Artifact>(`/portfolio-projects/${q(id)}/drafts`, json("POST", { kind })),
  readiness: (id: string) => request<Readiness>(`/portfolio-projects/${q(id)}/readiness`),
  evidenceProposals: (id: string) => request<unknown[]>(`/portfolio-projects/${q(id)}/evidence-proposals`),
};