export type BookSkillReviewAction =
  | "approve"
  | "reject";

export type BookSkillMappingStatus =
  | "generating"
  | "pending"
  | "approved"
  | "rejected"
  | "failed";

export interface BookSkillMapping {
  mapping_id: string;

  document_id: string;
  skill_id: string;

  mapping_status: string;
  coverage_level: string | null;

  is_primary_skill: boolean;

  relevance_score: number | null;
  coverage_score: number | null;
  depth_score: number | null;
  practicality_score: number | null;

  confidence: number | null;

  recommended_entry_level_id:
    | string
    | null;

  recommended_exit_level_id:
    | string
    | null;

  coverage_summary: string | null;

  learning_outcomes: string[] | null;
  covered_topics: string[] | null;
  limitations: string[] | null;

  mapping_source: string;
  mapping_model: string | null;
  mapping_version: number;

  candidate_payload:
    | Record<string, unknown>
    | null;

  candidate_error: string | null;

  candidate_generated_at: string | null;

  review_notes: string | null;
  reviewed_at: string | null;

  created_at: string;
  updated_at: string;
}

export interface BookSkillEvidence {
  evidence_type: string;

  chapter_title: string | null;
  section_title: string | null;

  page_start: number | null;
  page_end: number | null;

  chunk_id: string | null;
  excerpt: string | null;

  source_locator:
    | Record<string, unknown>
    | null;

  confidence: number | null;
  display_order: number;

  evidence_id: string;
  mapping_id: string;
  created_at: string;
}

export interface ProficiencyLevelSummary {
  level_id: string;
  code: string;
  name: string;
  level_order: number;
}

export interface BookSkillReview {
  mapping: BookSkillMapping;

  document_id: string;
  document_title: string;

  skill_id: string;
  skill_slug: string;
  skill_name: string;

  domain_name: string;
  category_name: string | null;

  candidate:
    | Record<string, unknown>
    | null;

  trusted_evidence: BookSkillEvidence[];

  entry_level:
    | ProficiencyLevelSummary
    | null;

  exit_level:
    | ProficiencyLevelSummary
    | null;

  reviewed_action: string | null;
}

export interface BookSkillReviewQueue {
  document_id: string;
  result_count: number;
  reviews: BookSkillReview[];
}

export interface BookSkillReviewRequest {
  action: BookSkillReviewAction;

  edited_candidate?:
    | Record<string, unknown>
    | null;

  review_notes: string | null;
}

export interface BookSkillReviewResult {
  mapping_id: string;
  action: BookSkillReviewAction;

  final_status: string;
  evidence_created: number;

  reviewed_at: string;

  review: BookSkillReview;
}