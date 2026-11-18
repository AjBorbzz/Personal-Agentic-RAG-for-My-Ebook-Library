// Phase 13G frontend projections of Phase 13E and 13F API fields.
// UUIDs and canonical proficiency/skill IDs are strings over HTTP.
export type Profile = {
  profile_id: string;
  profile_name: string;
  description: string | null;
  is_default: boolean;
  is_active: boolean;
};

export type SkillState = {
  profile_skill_id: string;
  profile_id: string;
  skill_id: string;
  current_level_id: string | null;
  target_level_id: string | null;
  confidence: number | string | null;
  career_priority: number;
  learning_status: string;
  last_assessed_at?: string | null;
  notes: string | null;
};

export type ProficiencyLevel = {
  level_id: string;
  code: string;
  name: string;
  level_order: number;
};

export type CanonicalSkill = { skill_id: string; name: string; slug?: string };

export type CareerTarget = {
  career_target_id: string;
  profile_id: string;
  role_name: string;
  role_slug: string;
  description: string | null;
  priority: number;
  status: string;
  target_date: string | null;
  created_at?: string;
  updated_at?: string;
};

export type CareerTargetSkill = {
  career_target_skill_id: string;
  career_target_id: string;
  skill_id: string;
  required_level_id: string;
  importance_weight: number;
  is_required: boolean;
  rationale: string | null;
};

export type Evidence = {
  evidence_id: string;
  profile_skill_id: string;
  evidence_type: string;
  title: string;
  description: string | null;
  verification_status: string;
  source_url: string | null;
  source_document_id: string | null;
  created_at: string;
  updated_at: string;
};

export type GapItem = {
  skill_id: string;
  skill_name: string;
  current_level: string | null;
  target_level: string | null;
  gap_steps: number | null;
  career_importance: number | null;
  confidence: number | string | null;
  gap_type: string;
  missing_prerequisite_skill_ids: string[];
  approved_supporting_book_count: number;
  explanation: string;
};

export type GapResponse = {
  profile_id: string;
  career_target_id: string | null;
  summary: {
    tracked_skills: number; target_skills: number;
    met_or_exceeded: number; level_gaps: number;
    unknown_current_level: number; missing_prerequisites: number;
  };
  gaps: GapItem[];
};

export type DecisionStatus = "new" | "accepted" | "deferred" | "dismissed" | "completed";
export type QueueStatus = "queued" | "active" | "paused" | "completed" | "removed";
export type Recommendation = {
  recommendation_id: string;
  recommendation_run_id: string;
  skill_id: string;
  recommendation_type: string;
  priority_score: number | string;
  score_components: Record<string, unknown>;
  source_mapping_ids: string[];
  recommended_document_id: string | null;
  title: string;
  explanation: string;
  decision_status: DecisionStatus;
  decision_notes: string | null;
};
export type RecommendationRunDetail = {
  run: { recommendation_run_id: string; profile_id: string; rule_version: string; status: string };
  items: Recommendation[];
};
export type QueueItem = {
  reading_queue_item_id: string;
  profile_id: string;
  document_id: string | null;
  skill_id: string | null;
  recommendation_id: string | null;
  status: QueueStatus;
  priority: number;
  planned_start: string | null;
  target_finish: string | null;
  progress_percent: number;
  notes: string | null;
};