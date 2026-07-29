"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  apiGet,
  apiPatch,
  apiPost,
} from "@/lib/api";


type EnrichedBookMetadata = {
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


type DocumentRecord = {
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


type MetadataReviewState = {
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


type MetadataCandidateResponse = {
  document_id: string;
  review_status: string;

  candidate: EnrichedBookMetadata;
  proposed_updates: Record<string, unknown>;

  source_characters_used: number;
  source_was_truncated: boolean;
  warnings: string[];

  document: DocumentRecord;
};


type QdrantSyncResponse = {
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


type MetadataReviewResponse = {
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


type StageCandidateRequest = {
  overwrite_existing: boolean;
  max_source_characters: number;
};


type ReviewRequest = {
  action: "approve" | "reject";
  overwrite_existing: boolean;
  sync_to_qdrant: boolean;
  review_notes: string | null;
  edited_candidate?: EnrichedBookMetadata;
};


type SyncRequest = {
  force: boolean;
  create_payload_indexes: boolean;
};


const EMPTY_CANDIDATE: EnrichedBookMetadata = {
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


function parseList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}


function formatList(values: string[] | null | undefined) {
  return (values || []).join(", ");
}


function formatDate(value: string | null | undefined) {
  if (!value) {
    return "N/A";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}


function ReviewStatusBadge({
  status,
}: {
  status: string;
}) {
  const styles: Record<string, string> = {
    not_requested:
      "border-neutral-700 bg-neutral-900 text-neutral-300",
    pending:
      "border-yellow-800 bg-yellow-950 text-yellow-300",
    approved:
      "border-green-800 bg-green-950 text-green-300",
    rejected:
      "border-red-800 bg-red-950 text-red-300",
  };

  const style =
    styles[status] ??
    "border-neutral-700 bg-neutral-900 text-neutral-300";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}


function TextField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-neutral-300">
        {label}
      </label>

      <input
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(event) =>
          onChange(event.target.value || null)
        }
        className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
      />
    </div>
  );
}


function ListField({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-neutral-300">
        {label}
      </label>

      <textarea
        value={formatList(values)}
        placeholder={placeholder}
        rows={3}
        onChange={(event) =>
          onChange(parseList(event.target.value))
        }
        className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
      />

      <p className="mt-1 text-xs text-neutral-500">
        Separate values with commas.
      </p>
    </div>
  );
}


function ExistingValue({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  let displayValue = "N/A";

  if (Array.isArray(value)) {
    displayValue = value.join(", ") || "N/A";
  } else if (
    value !== null &&
    value !== undefined &&
    value !== ""
  ) {
    displayValue = String(value);
  }

  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-950 p-3">
      <p className="text-xs uppercase tracking-wide text-neutral-500">
        {label}
      </p>

      <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-300">
        {displayValue}
      </p>
    </div>
  );
}


export default function MetadataEditorPage() {
  const params = useParams();
  const documentId = params.documentId as string;

  const [reviewState, setReviewState] =
    useState<MetadataReviewState | null>(null);

  const [candidate, setCandidate] =
    useState<EnrichedBookMetadata>(
      EMPTY_CANDIDATE
    );

  const [overwriteExisting, setOverwriteExisting] =
    useState(false);

  const [syncToQdrant, setSyncToQdrant] =
    useState(true);

  const [maxSourceCharacters, setMaxSourceCharacters] =
    useState(24000);

  const [reviewNotes, setReviewNotes] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [generating, setGenerating] =
    useState(false);

  const [reviewing, setReviewing] =
    useState(false);

  const [syncing, setSyncing] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [message, setMessage] =
    useState<string | null>(null);

  const [warnings, setWarnings] =
    useState<string[]>([]);

  const [syncResult, setSyncResult] =
    useState<QdrantSyncResponse | null>(null);


  const loadReviewState = useCallback(async () => {
    if (!documentId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data =
        await apiGet<MetadataReviewState>(
          `/documents/${documentId}/metadata-review`
        );

      setReviewState(data);
      setReviewNotes(data.review_notes ?? "");

      if (data.candidate) {
        setCandidate(data.candidate);
      } else {
        setCandidate(EMPTY_CANDIDATE);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load metadata review."
      );
    } finally {
      setLoading(false);
    }
  }, [documentId]);


  useEffect(() => {
    void loadReviewState();
  }, [loadReviewState]);


  const document = reviewState?.document ?? null;


  const candidateChanged = useMemo(() => {
    if (!reviewState?.candidate) {
      return false;
    }

    return (
      JSON.stringify(candidate) !==
      JSON.stringify(reviewState.candidate)
    );
  }, [candidate, reviewState]);


  function updateCandidate<K extends keyof EnrichedBookMetadata>(
    field: K,
    value: EnrichedBookMetadata[K]
  ) {
    setCandidate((current) => ({
      ...current,
      [field]: value,
    }));
  }


  async function generateCandidate() {
    setGenerating(true);
    setError(null);
    setMessage(null);
    setWarnings([]);
    setSyncResult(null);

    try {
      const response =
        await apiPost<
          MetadataCandidateResponse,
          StageCandidateRequest
        >(
          `/documents/${documentId}/metadata-candidate`,
          {
            overwrite_existing: overwriteExisting,
            max_source_characters:
              maxSourceCharacters,
          }
        );

      setCandidate(response.candidate);
      setWarnings(response.warnings);
      setMessage(
        "Metadata candidate generated and staged for review."
      );

      await loadReviewState();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate metadata candidate."
      );
    } finally {
      setGenerating(false);
    }
  }


  async function approveCandidate() {
    const confirmed = window.confirm(
      "Approve this metadata candidate and apply it to the document?"
    );

    if (!confirmed) {
      return;
    }

    setReviewing(true);
    setError(null);
    setMessage(null);
    setWarnings([]);
    setSyncResult(null);

    try {
      const response =
        await apiPatch<
          MetadataReviewResponse,
          ReviewRequest
        >(
          `/documents/${documentId}/metadata-review`,
          {
            action: "approve",
            overwrite_existing: overwriteExisting,
            sync_to_qdrant: syncToQdrant,
            review_notes:
              reviewNotes.trim() || null,
            edited_candidate: candidate,
          }
        );

      setWarnings(response.warnings || []);
      setSyncResult(response.qdrant_sync);

      setMessage(
        response.applied
          ? `Metadata approved. Updated fields: ${response.updated_fields.join(", ")}`
          : "Metadata approved, but no document fields required changes."
      );

      await loadReviewState();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to approve metadata."
      );
    } finally {
      setReviewing(false);
    }
  }


  async function rejectCandidate() {
    const confirmed = window.confirm(
      "Reject this metadata candidate?"
    );

    if (!confirmed) {
      return;
    }

    setReviewing(true);
    setError(null);
    setMessage(null);
    setWarnings([]);
    setSyncResult(null);

    try {
      const response =
        await apiPatch<
          MetadataReviewResponse,
          ReviewRequest
        >(
          `/documents/${documentId}/metadata-review`,
          {
            action: "reject",
            overwrite_existing: false,
            sync_to_qdrant: false,
            review_notes:
              reviewNotes.trim() || null,
          }
        );

      setMessage(
        `Metadata candidate ${response.review_status}.`
      );

      await loadReviewState();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to reject metadata."
      );
    } finally {
      setReviewing(false);
    }
  }


  async function synchronizeQdrant() {
    setSyncing(true);
    setError(null);
    setMessage(null);
    setWarnings([]);
    setSyncResult(null);

    try {
      const response =
        await apiPost<
          QdrantSyncResponse,
          SyncRequest
        >(
          `/documents/${documentId}/sync-qdrant`,
          {
            force: false,
            create_payload_indexes: true,
          }
        );

      setSyncResult(response);
      setWarnings(response.warnings || []);

      setMessage(
        `Synchronized metadata to ${response.matched_points} Qdrant chunk(s).`
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to synchronize Qdrant."
      );
    } finally {
      setSyncing(false);
    }
  }


  if (loading) {
    return (
      <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
        <div className="mx-auto max-w-7xl">
          Loading metadata review…
        </div>
      </main>
    );
  }


  if (!reviewState || !document) {
    return (
      <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
        <div className="mx-auto max-w-7xl">
          <p>Document metadata could not be loaded.</p>

          {error && (
            <pre className="mt-4 whitespace-pre-wrap rounded-xl border border-red-900 bg-red-950 p-4 text-sm text-red-200">
              {error}
            </pre>
          )}
        </div>
      </main>
    );
  }


  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-7xl">
        <div>
          <Link
            href="/documents"
            className="text-sm text-neutral-400 hover:text-white"
          >
            ← Back to Document Library
          </Link>

          <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-3xl font-bold">
                  Metadata Review
                </h1>

                <ReviewStatusBadge
                  status={reviewState.review_status}
                />
              </div>

              <p className="mt-3 text-neutral-400">
                {document.title ||
                  document.filename ||
                  "Untitled document"}
              </p>

              <p className="mt-1 break-all font-mono text-xs text-neutral-600">
                {document.document_id}
              </p>
            </div>

            <button
              type="button"
              onClick={() => void generateCandidate()}
              disabled={generating}
              className="rounded-xl bg-white px-5 py-2 text-sm font-medium text-black disabled:opacity-50"
            >
              {generating
                ? "Generating…"
                : reviewState.candidate
                  ? "Regenerate Candidate"
                  : "Generate Candidate"}
            </button>
          </div>
        </div>


        {error && (
          <pre className="mt-6 overflow-auto whitespace-pre-wrap rounded-xl border border-red-900 bg-red-950 p-4 text-sm text-red-200">
            {error}
          </pre>
        )}


        {message && (
          <div className="mt-6 rounded-xl border border-green-900 bg-green-950 p-4 text-sm text-green-200">
            {message}
          </div>
        )}


        {warnings.length > 0 && (
          <div className="mt-6 rounded-xl border border-yellow-900 bg-yellow-950 p-4">
            <p className="font-medium text-yellow-300">
              Warnings
            </p>

            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-yellow-200">
              {warnings.map((warning) => (
                <li key={warning}>
                  {warning}
                </li>
              ))}
            </ul>
          </div>
        )}


        <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <h2 className="text-lg font-semibold">
            Generation Settings
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <label className="flex items-center gap-3 rounded-xl border border-neutral-700 bg-neutral-950 p-4">
              <input
                type="checkbox"
                checked={overwriteExisting}
                onChange={(event) =>
                  setOverwriteExisting(
                    event.target.checked
                  )
                }
              />

              <span className="text-sm text-neutral-300">
                Allow approved metadata to overwrite existing values
              </span>
            </label>

            <label className="flex items-center gap-3 rounded-xl border border-neutral-700 bg-neutral-950 p-4">
              <input
                type="checkbox"
                checked={syncToQdrant}
                onChange={(event) =>
                  setSyncToQdrant(
                    event.target.checked
                  )
                }
              />

              <span className="text-sm text-neutral-300">
                Synchronize to Qdrant after approval
              </span>
            </label>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Source Character Limit
              </label>

              <input
                type="number"
                min={4000}
                max={60000}
                step={1000}
                value={maxSourceCharacters}
                onChange={(event) =>
                  setMaxSourceCharacters(
                    Number(event.target.value)
                  )
                }
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
              />
            </div>
          </div>
        </section>


        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <h2 className="text-xl font-semibold">
              Existing Trusted Metadata
            </h2>

            <p className="mt-2 text-sm text-neutral-500">
              Current values stored in PostgreSQL.
            </p>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <ExistingValue
                label="Title"
                value={document.title}
              />

              <ExistingValue
                label="Author"
                value={document.author}
              />

              <ExistingValue
                label="Subtitle"
                value={document.subtitle}
              />

              <ExistingValue
                label="Publisher"
                value={document.publisher}
              />

              <ExistingValue
                label="Edition"
                value={document.edition}
              />

              <ExistingValue
                label="Language"
                value={document.language}
              />

              <ExistingValue
                label="Publication Year"
                value={document.publication_year}
              />

              <ExistingValue
                label="Difficulty"
                value={document.difficulty_level}
              />

              <ExistingValue
                label="ISBN-10"
                value={document.isbn_10}
              />

              <ExistingValue
                label="ISBN-13"
                value={document.isbn_13}
              />

              <ExistingValue
                label="Topics"
                value={document.topics}
              />

              <ExistingValue
                label="Technologies"
                value={document.technologies}
              />

              <ExistingValue
                label="Tags"
                value={document.tags}
              />

              <ExistingValue
                label="Prerequisites"
                value={
                  document.prerequisite_skills
                }
              />
            </div>

            <div className="mt-3">
              <ExistingValue
                label="Description"
                value={document.description}
              />
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <ExistingValue
                label="Metadata Source"
                value={document.metadata_source}
              />

              <ExistingValue
                label="Confidence"
                value={document.metadata_confidence}
              />

              <ExistingValue
                label="Enriched"
                value={formatDate(
                  document.enriched_at
                )}
              />

              <ExistingValue
                label="Reviewed"
                value={formatDate(
                  document.metadata_reviewed_at
                )}
              />
            </div>
          </div>


          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">
                  Candidate Metadata
                </h2>

                <p className="mt-2 text-sm text-neutral-500">
                  Review and edit before approval.
                </p>
              </div>

              {candidateChanged && (
                <span className="rounded-full border border-blue-800 bg-blue-950 px-2.5 py-1 text-xs text-blue-300">
                  Edited
                </span>
              )}
            </div>

            {!reviewState.candidate ? (
              <div className="mt-5 rounded-xl border border-neutral-800 bg-neutral-950 p-6 text-sm text-neutral-400">
                No candidate has been generated yet.
              </div>
            ) : (
              <div className="mt-5 space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <TextField
                    label="Title"
                    value={candidate.title}
                    onChange={(value) =>
                      updateCandidate(
                        "title",
                        value
                      )
                    }
                  />

                  <TextField
                    label="Author"
                    value={candidate.author}
                    onChange={(value) =>
                      updateCandidate(
                        "author",
                        value
                      )
                    }
                  />

                  <TextField
                    label="Subtitle"
                    value={candidate.subtitle}
                    onChange={(value) =>
                      updateCandidate(
                        "subtitle",
                        value
                      )
                    }
                  />

                  <TextField
                    label="Publisher"
                    value={candidate.publisher}
                    onChange={(value) =>
                      updateCandidate(
                        "publisher",
                        value
                      )
                    }
                  />

                  <TextField
                    label="Edition"
                    value={candidate.edition}
                    onChange={(value) =>
                      updateCandidate(
                        "edition",
                        value
                      )
                    }
                  />

                  <TextField
                    label="Language"
                    value={candidate.language}
                    onChange={(value) =>
                      updateCandidate(
                        "language",
                        value
                      )
                    }
                  />

                  <TextField
                    label="ISBN-10"
                    value={candidate.isbn_10}
                    onChange={(value) =>
                      updateCandidate(
                        "isbn_10",
                        value
                      )
                    }
                  />

                  <TextField
                    label="ISBN-13"
                    value={candidate.isbn_13}
                    onChange={(value) =>
                      updateCandidate(
                        "isbn_13",
                        value
                      )
                    }
                  />

                  <div>
                    <label className="block text-sm font-medium text-neutral-300">
                      Publication Year
                    </label>

                    <input
                      type="number"
                      min={1000}
                      max={2100}
                      value={
                        candidate.publication_year ??
                        ""
                      }
                      onChange={(event) =>
                        updateCandidate(
                          "publication_year",
                          event.target.value
                            ? Number(
                                event.target.value
                              )
                            : null
                        )
                      }
                      className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-300">
                      Difficulty
                    </label>

                    <select
                      value={
                        candidate.difficulty_level ??
                        "unknown"
                      }
                      onChange={(event) =>
                        updateCandidate(
                          "difficulty_level",
                          event.target.value
                        )
                      }
                      className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
                    >
                      <option value="unknown">
                        Unknown
                      </option>

                      <option value="beginner">
                        Beginner
                      </option>

                      <option value="intermediate">
                        Intermediate
                      </option>

                      <option value="advanced">
                        Advanced
                      </option>

                      <option value="mixed">
                        Mixed
                      </option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-300">
                    Description
                  </label>

                  <textarea
                    rows={5}
                    value={
                      candidate.description ?? ""
                    }
                    onChange={(event) =>
                      updateCandidate(
                        "description",
                        event.target.value || null
                      )
                    }
                    className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
                  />
                </div>

                <ListField
                  label="Topics"
                  values={candidate.topics}
                  onChange={(values) =>
                    updateCandidate(
                      "topics",
                      values
                    )
                  }
                  placeholder="authentication, api design, distributed systems"
                />

                <ListField
                  label="Technologies"
                  values={candidate.technologies}
                  onChange={(values) =>
                    updateCandidate(
                      "technologies",
                      values
                    )
                  }
                  placeholder="python, fastapi, postgresql"
                />

                <ListField
                  label="Tags"
                  values={candidate.tags}
                  onChange={(values) =>
                    updateCandidate(
                      "tags",
                      values
                    )
                  }
                  placeholder="backend, system-design, security"
                />

                <ListField
                  label="Prerequisite Skills"
                  values={
                    candidate.prerequisite_skills
                  }
                  onChange={(values) =>
                    updateCandidate(
                      "prerequisite_skills",
                      values
                    )
                  }
                  placeholder="python fundamentals, databases"
                />

                <div>
                  <label className="block text-sm font-medium text-neutral-300">
                    Confidence:{" "}
                    {candidate.metadata_confidence.toFixed(
                      2
                    )}
                  </label>

                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={
                      candidate.metadata_confidence
                    }
                    onChange={(event) =>
                      updateCandidate(
                        "metadata_confidence",
                        Number(event.target.value)
                      )
                    }
                    className="mt-3 w-full"
                  />
                </div>
              </div>
            )}
          </div>
        </section>


        {reviewState.candidate && (
          <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <h2 className="text-xl font-semibold">
              Review Decision
            </h2>

            <div className="mt-5">
              <label className="block text-sm font-medium text-neutral-300">
                Review Notes
              </label>

              <textarea
                rows={4}
                value={reviewNotes}
                onChange={(event) =>
                  setReviewNotes(event.target.value)
                }
                placeholder="Describe corrections, concerns, or approval reasoning."
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
              />
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() =>
                  void approveCandidate()
                }
                disabled={reviewing}
                className="rounded-xl bg-green-200 px-5 py-2 text-sm font-medium text-green-950 disabled:opacity-50"
              >
                {reviewing
                  ? "Processing…"
                  : "Approve Metadata"}
              </button>

              <button
                type="button"
                onClick={() =>
                  void rejectCandidate()
                }
                disabled={reviewing}
                className="rounded-xl border border-red-800 px-5 py-2 text-sm font-medium text-red-300 disabled:opacity-50"
              >
                Reject Candidate
              </button>
            </div>
          </section>
        )}


        {reviewState.review_status ===
          "approved" && (
          <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">
                  Qdrant Synchronization
                </h2>

                <p className="mt-2 text-sm text-neutral-500">
                  Copy approved PostgreSQL metadata to every indexed chunk.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  void synchronizeQdrant()
                }
                disabled={syncing}
                className="rounded-xl border border-blue-800 px-5 py-2 text-sm text-blue-300 disabled:opacity-50"
              >
                {syncing
                  ? "Synchronizing…"
                  : "Synchronize Qdrant"}
              </button>
            </div>

            {syncResult && (
              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <ExistingValue
                  label="Collection"
                  value={
                    syncResult.collection_name
                  }
                />

                <ExistingValue
                  label="Matched Chunks"
                  value={
                    syncResult.matched_points
                  }
                />

                <ExistingValue
                  label="Payload Keys Set"
                  value={
                    syncResult.payload_keys_set
                  }
                />

                <ExistingValue
                  label="Indexes Created"
                  value={
                    syncResult.created_indexes
                  }
                />
              </div>
            )}
          </section>
        )}


        <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <h2 className="text-xl font-semibold">
            Proposed Updates
          </h2>

          <pre className="mt-4 overflow-auto whitespace-pre-wrap rounded-xl border border-neutral-800 bg-neutral-950 p-4 text-xs text-neutral-400">
            {JSON.stringify(
              reviewState.proposed_updates,
              null,
              2
            )}
          </pre>
        </section>
      </section>
    </main>
  );
}