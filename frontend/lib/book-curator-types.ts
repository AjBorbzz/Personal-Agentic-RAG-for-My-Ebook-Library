export type RankingPurpose =
  | "general"
  | "learning"
  | "project"
  | "reference"
  | "current_technology"
  | "foundational";

export interface DashboardStats {
  total_documents: number;
  active_documents: number;
  deprecated_documents: number;

  approved_evaluations: number;
  pending_evaluations: number;
  generating_evaluations: number;
  failed_evaluations: number;
  rejected_evaluations: number;
  not_evaluated: number;

  essential_books: number;
  top_pick_books: number;

  pending_relationships: number;
  exact_duplicates: number;
  different_editions: number;
  high_content_overlaps: number;
}

export interface RankingBreakdown {
  purpose_base_score: number;
  priority_modifier: number;
  role_modifier: number;
  audience_modifier: number;
  lifecycle_modifier: number;
  relationship_modifier: number;
  final_score: number;
}

export interface RankedBook {
  document_id: string;
  curation_id: string | null;

  filename: string | null;
  title: string | null;
  author: string | null;
  publication_year: number | null;

  primary_domain: string | null;
  domains: string[];
  topics: string[];
  technologies: string[];

  is_active: boolean;
  is_deprecated: boolean;

  evaluation_status: string;
  overall_score: number | null;

  audience_level: string | null;
  recommended_role: string | null;
  library_priority: string | null;

  ranking_purpose: RankingPurpose;
  ranking_score: number;
  recommendation_tier: string;

  breakdown: RankingBreakdown;
  reasons: string[];
  warnings: string[];
}

export interface ReviewQueueItem {
  document_id: string;
  curation_id: string | null;

  filename: string | null;
  title: string | null;
  author: string | null;
  publication_year: number | null;

  evaluation_status: string;
  overall_score: number | null;

  audience_level: string | null;
  recommended_role: string | null;
  library_priority: string | null;

  evaluation_model: string | null;
  evaluation_error: string | null;

  evaluated_at: string | null;
  reviewed_at: string | null;
  updated_at: string | null;
}

export interface BookRelationship {
  relationship_id: string;
  pair_key: string;

  document_a_id: string;
  document_b_id: string;

  relationship_type: string;
  status: string;

  exact_hash_match: boolean;
  isbn_match: boolean;

  title_similarity: number | null;
  author_similarity: number | null;
  metadata_overlap_score: number | null;
  content_overlap_score: number | null;

  confidence: number;

  reasons: string[] | null;

  document_a_snapshot:
    | Record<string, unknown>
    | null;

  document_b_snapshot:
    | Record<string, unknown>
    | null;

  recommended_primary_document_id:
    | string
    | null;

  recommended_superseded_document_id:
    | string
    | null;

  recommended_action: string | null;

  detector_version: number;

  review_notes: string | null;
  reviewed_at: string | null;

  created_at: string;
  updated_at: string;
}

export interface BookCuratorDashboard {
  generated_at: string;

  purpose: RankingPurpose;

  filters: {
    domain: string | null;
    topic: string | null;
    technology: string | null;
    audience_level: string | null;
  };

  stats: DashboardStats;

  top_books: RankedBook[];
  review_queue: ReviewQueueItem[];

  pending_relationships: BookRelationship[];

  warnings: string[];
}