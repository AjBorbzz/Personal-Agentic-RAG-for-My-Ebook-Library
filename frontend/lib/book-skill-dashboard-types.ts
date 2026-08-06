export interface BookSkillDomainOption {
  slug: string;
  name: string;
}

export interface BookSkillDashboardStats {
  registered_documents: number;

  books_with_any_mappings: number;
  books_with_approved_mappings: number;

  total_mappings: number;
  pending_mappings: number;
  approved_mappings: number;
  rejected_mappings: number;
  failed_mappings: number;

  primary_mappings: number;

  active_skills: number;
  skills_with_approved_books: number;
  unmapped_active_skills: number;
}

export interface BookSkillStatusCount {
  status: string;
  count: number;
}

export interface BookCoverageSummary {
  document_id: string;
  document_title: string;
  author: string | null;

  approved_mapping_count: number;
  primary_skill_count: number;

  average_quality_score: number;
  average_relevance_score: number;
  average_coverage_score: number;
  average_depth_score: number;
  average_practicality_score: number;

  primary_skills: string[];
}

export interface SkillCoverageSummary {
  skill_id: string;
  skill_slug: string;
  skill_name: string;

  domain_name: string;
  category_name: string | null;

  supporting_book_count: number;
  primary_book_count: number;

  average_quality_score: number;
  average_relevance_score: number;
  average_coverage_score: number;
  average_depth_score: number;
  average_practicality_score: number;

  best_document_id: string | null;
  best_document_title: string | null;
  best_document_score: number | null;
}

export interface PendingBookSkillReview {
  mapping_id: string;

  document_id: string;
  document_title: string;

  skill_id: string;
  skill_name: string;

  domain_name: string;
  category_name: string | null;

  mapping_version: number;
  mapping_model: string | null;

  candidate_generated_at: string | null;
  updated_at: string;
}

export interface UnmappedSkillSummary {
  skill_id: string;
  skill_slug: string;
  skill_name: string;

  domain_name: string;
  category_name: string | null;

  skill_type: string;
  difficulty_level: string;
}

export interface BookSkillDashboard {
  domain_filter: string | null;

  domains: BookSkillDomainOption[];

  stats: BookSkillDashboardStats;

  status_counts: BookSkillStatusCount[];

  top_books: BookCoverageSummary[];
  top_skills: SkillCoverageSummary[];

  pending_reviews:
    PendingBookSkillReview[];

  unmapped_skills:
    UnmappedSkillSummary[];
}