export type EnrichedBookMetadata = {
  title: string | null;
  author: string | null;
  subtitle: string | null;
  publisher: string | null;
  edition: string | null;

  isbn_10: string | null;
  isbn_13: string | null;
  language: string | null;
  publication_year: number | null;

  description: string | null;
  difficulty_level: string | null;

  topics: string[];
  technologies: string[];
  tags: string[];
  prerequisite_skills: string[];

  metadata_confidence: number;
};

export type DocumentRecord = {
  document_id: string;

  filename: string | null;
  title: string | null;
  author: string | null;
  subtitle: string | null;
  publisher: string | null;
  edition: string | null;

  isbn_10: string | null;
  isbn_13: string | null;
  language: string | null;

  description: string | null;
  difficulty_level: string | null;

  publication_year: number | null;

  primary_domain: string | null;
  domains: string[] | null;

  topics: string[] | null;
  technologies: string[] | null;
  tags: string[] | null;
  prerequisite_skills: string[] | null;

  metadata_source: string | null;
  metadata_confidence: number | null;
  metadata_reviewed: boolean;
  metadata_review_status: string;
  metadata_review_notes: string | null;

  enriched_at: string | null;
  metadata_reviewed_at: string | null;

  is_active: boolean;
  is_deprecated: boolean;
};

export type MetadataReviewState = {
  document_id: string;
  review_status: string;

  candidate: EnrichedBookMetadata | null;
  proposed_updates: Record<string, unknown>;

  review_notes: string | null;
  metadata_confidence: number | null;
  enriched_at: string | null;
  reviewed_at: string | null;

  document: DocumentRecord;
};

export type MetadataCandidateResponse = {
  document_id: string;
  review_status: string;

  candidate: EnrichedBookMetadata;
  proposed_updates: Record<string, unknown>;

  source_characters_used: number;
  source_was_truncated: boolean;
  warnings: string[];

  document: DocumentRecord;
};

export type QdrantSyncResponse = {
  document_id: string;
  collection_name: string;

  matched_points: number;
  payload_keys_set: string[];
  payload_keys_deleted: string[];
  created_indexes: string[];

  metadata_review_status: string;
  metadata_reviewed: boolean;

  synced_at: string;
  warnings: string[];
};

export type MetadataReviewResponse = {
  document_id: string;
  action: "approve" | "reject";
  review_status: string;

  applied: boolean;
  updated_fields: string[];

  candidate: EnrichedBookMetadata | null;
  proposed_updates: Record<string, unknown>;

  qdrant_sync: QdrantSyncResponse | null;
  warnings: string[];

  document: DocumentRecord;
};

export type StageCandidateRequest = {
  overwrite_existing: boolean;
  max_source_characters: number;
};

export type ReviewRequest = {
  action: "approve" | "reject";
  overwrite_existing: boolean;
  sync_to_qdrant: boolean;
  review_notes: string | null;
  edited_candidate?: EnrichedBookMetadata;
};

export type SyncRequest = {
  force: boolean;
  create_payload_indexes: boolean;
};

export const EMPTY_CANDIDATE: EnrichedBookMetadata = {
  title: null,
  author: null,
  subtitle: null,
  publisher: null,
  edition: null,

  isbn_10: null,
  isbn_13: null,
  language: null,
  publication_year: null,

  description: null,
  difficulty_level: "unknown",

  topics: [],
  technologies: [],
  tags: [],
  prerequisite_skills: [],

  metadata_confidence: 0.5,
};
