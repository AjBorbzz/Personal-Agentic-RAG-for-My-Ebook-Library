"use client";

import Link from "next/link";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { DocumentReviewNav } from "../DocumentReviewNav";
import { useParams } from "next/navigation";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  fetchBookSkillReviewQueue,
  submitBookSkillReview,
} from "@/lib/book-skill-review-api";

import type {
  BookSkillEvidence,
  BookSkillReview,
  BookSkillReviewAction,
  BookSkillReviewQueue,
} from "@/lib/book-skill-review-types";

type ReviewFilter = "pending" | "approved" | "rejected" | "failed" | "all";

const PANEL_CLASS_NAME = "workspace-panel min-w-0";
const FIELD_CLASS_NAME = "workspace-field";
const SECONDARY_BUTTON_CLASS_NAME =
  "workspace-button workspace-button--secondary";

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatScore(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return `${Math.round(value)}/100`;
}

function formatConfidence(value: number | null): string {
  if (value === null) {
    return "—";
  }

  const percentage = value <= 1 ? value * 100 : value;

  return `${percentage.toFixed(1)}%`;
}

function isValidJson(value: string): boolean {
  if (!value.trim()) {
    return false;
  }

  try {
    const parsed: unknown = JSON.parse(value);

    return (
      typeof parsed === "object" && parsed !== null && !Array.isArray(parsed)
    );
  } catch {
    return false;
  }
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  let className = "border-neutral-700 bg-neutral-800 " + "text-neutral-300";

  if (normalized === "approved") {
    className =
      "border-emerald-900/70 " + "bg-emerald-950/60 " + "text-emerald-300";
  } else if (normalized === "pending" || normalized === "generating") {
    className = "border-amber-900/70 " + "bg-amber-950/60 " + "text-amber-300";
  } else if (normalized === "rejected" || normalized === "failed") {
    className = "border-red-900/70 " + "bg-red-950/60 " + "text-red-300";
  }

  return (
    <span
      className={
        "inline-flex rounded-full border " +
        "px-2.5 py-1 text-xs font-medium " +
        className
      }
    >
      {formatLabel(status)}
    </span>
  );
}

function DetailCard({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
        {label}
      </p>

      <div className="mt-2 text-sm font-medium text-neutral-200">{value}</div>
    </div>
  );
}

function QueueItem({
  review,
  selected,
  onSelect,
}: {
  review: BookSkillReview;
  selected: boolean;
  onSelect: (review: BookSkillReview) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(review)}
      className={
        "w-full rounded-xl border p-4 " +
        "text-left transition " +
        (selected
          ? "border-neutral-500 bg-neutral-800"
          : "border-neutral-800 bg-neutral-950/60 hover:bg-neutral-800/60")
      }
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-white">{review.skill_name}</p>

          <p className="mt-1 text-xs text-neutral-500">
            {review.domain_name}
            {review.category_name ? ` · ${review.category_name}` : ""}
          </p>
        </div>

        <StatusBadge status={review.mapping.mapping_status} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {review.mapping.coverage_level ? (
          <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
            {formatLabel(review.mapping.coverage_level)}
          </span>
        ) : null}

        {review.mapping.is_primary_skill ? (
          <span className="rounded-full border border-blue-900/70 bg-blue-950/50 px-2 py-0.5 text-xs text-blue-300">
            Primary skill
          </span>
        ) : null}

        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-500">
          Version {review.mapping.mapping_version}
        </span>
      </div>
    </button>
  );
}

function EvidenceCard({ evidence }: { evidence: BookSkillEvidence }) {
  const location = [evidence.chapter_title, evidence.section_title]
    .filter(Boolean)
    .join(" · ");

  const pageRange =
    evidence.page_start !== null
      ? evidence.page_end !== null && evidence.page_end !== evidence.page_start
        ? `Pages ${evidence.page_start}–${evidence.page_end}`
        : `Page ${evidence.page_start}`
      : null;

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
          {formatLabel(evidence.evidence_type)}
        </span>

        {pageRange ? (
          <span className="text-xs text-neutral-500">{pageRange}</span>
        ) : null}

        {evidence.confidence !== null ? (
          <span className="text-xs text-neutral-500">
            Confidence {formatConfidence(evidence.confidence)}
          </span>
        ) : null}
      </div>

      {location ? (
        <p className="mt-3 text-sm font-medium text-neutral-200">{location}</p>
      ) : null}

      {evidence.excerpt ? (
        <blockquote className="mt-3 border-l-2 border-neutral-700 pl-4 text-sm leading-6 text-neutral-400">
          {evidence.excerpt}
        </blockquote>
      ) : null}
    </div>
  );
}

export default function BookSkillReviewPage() {
  const { documentId } = useParams<{ documentId: string }>();
  return <BookSkillReviewEditor key={documentId} documentId={documentId} />;
}

function BookSkillReviewEditor({ documentId }: { documentId: string }) {
  const [revision, setRevision] = useState(0);
  const [queueError, setQueueError] = useState<string | null>(null);

  const [filter, setFilter] = useState<ReviewFilter>("pending");

  const [queue, setQueue] = useState<BookSkillReviewQueue | null>(null);

  const [selectedReview, setSelectedReview] = useState<BookSkillReview | null>(
    null,
  );

  const [candidateJson, setCandidateJson] = useState("");

  const [reviewNotes, setReviewNotes] = useState("");

  const [loading, setLoading] = useState(true);

  const [savingAction, setSavingAction] =
    useState<BookSkillReviewAction | null>(null);

  const [error, setError] = useState<string | null>(null);

  const [message, setMessage] = useState<string | null>(null);

  const candidateIsValid = useMemo(
    () => isValidJson(candidateJson),
    [candidateJson],
  );

  const synchronizeEditor = useCallback((review: BookSkillReview | null) => {
    setSelectedReview(review);

    setCandidateJson(
      review?.candidate ? JSON.stringify(review.candidate, null, 2) : "",
    );

    setReviewNotes(review?.mapping.review_notes ?? "");
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchBookSkillReviewQueue(documentId, filter, { signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted) return;

        setQueue(result);
        synchronizeEditor(result.reviews[0] ?? null);
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setQueueError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load the review queue.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [documentId, filter, revision, synchronizeEditor]);

  function refreshQueue() {
    setLoading(true);
    setQueueError(null);
    setRevision((current) => current + 1);
  }

  async function submitReview(action: BookSkillReviewAction) {
    if (!selectedReview) {
      return;
    }

    setSavingAction(action);
    setError(null);
    setMessage(null);

    try {
      let editedCandidate: Record<string, unknown> | undefined;

      if (action === "approve") {
        if (!candidateJson.trim()) {
          throw new Error("The candidate payload is empty.");
        }

        try {
          editedCandidate = JSON.parse(candidateJson) as Record<
            string,
            unknown
          >;
        } catch {
          throw new Error("The candidate payload is not valid JSON.");
        }
      }

      const result = await submitBookSkillReview(
        selectedReview.mapping.mapping_id,
        {
          action,
          edited_candidate: action === "approve" ? editedCandidate : undefined,
          review_notes: reviewNotes.trim() || null,
        },
      );

      setMessage(
        action === "approve"
          ? `Approved ${result.review.skill_name}.`
          : `Rejected ${result.review.skill_name}.`,
      );

      const refreshedQueue = await fetchBookSkillReviewQueue(
        documentId,
        filter,
      );

      setQueue(refreshedQueue);

      const refreshedSelection =
        refreshedQueue.reviews.find(
          (review) => review.mapping.mapping_id === result.mapping_id,
        ) ??
        refreshedQueue.reviews[0] ??
        result.review;

      synchronizeEditor(refreshedSelection);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to submit the review.",
      );
    } finally {
      setSavingAction(null);
    }
  }

  const busy = loading || savingAction !== null;

  return (
    <PageFrame width="wide" className="space-y-6">
      <PageHeader
        title="Book-to-Skill Review"
        description="Review each AI-generated mapping before it becomes trusted evidence of what the book can teach."
        back={{ label: "Document Library", href: "/documents" }}
      >
        <p className="mt-3 break-all font-mono text-xs text-neutral-400">
          Document ID: {documentId}
        </p>
        <DocumentReviewNav documentId={documentId} />
      </PageHeader>

      {queueError && <StatusMessage tone="error">{queueError}</StatusMessage>}
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {message && <StatusMessage tone="success">{message}</StatusMessage>}

      <section className={PANEL_CLASS_NAME}>
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
              Review queue
            </p>

            <h2 className="mt-2 text-xl font-semibold text-white">
              Mapping status
            </h2>

            <p className="mt-2 text-sm text-neutral-400">
              Select which mapping state should be displayed.
            </p>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <Field label="Mapping status">
              <select
                value={filter}
                disabled={savingAction !== null}
                onChange={(event) => {
                  setLoading(true);
                  setQueueError(null);
                  setQueue(null);
                  synchronizeEditor(null);
                  setFilter(event.target.value as ReviewFilter);
                }}
                className="workspace-field"
              >
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="failed">Failed</option>
                <option value="all">All mappings</option>
              </select>
            </Field>
            <button
              type="button"
              disabled={busy}
              onClick={refreshQueue}
              className={SECONDARY_BUTTON_CLASS_NAME}
            >
              Refresh
            </button>
            <Link
              href="/book-skill-dashboard"
              className={SECONDARY_BUTTON_CLASS_NAME}
            >
              Skill dashboard
            </Link>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <DetailCard
            label="Visible mappings"
            value={queue?.result_count ?? 0}
          />

          <DetailCard label="Current filter" value={formatLabel(filter)} />

          <DetailCard
            label="Selected skill"
            value={selectedReview?.skill_name ?? "None"}
          />
        </div>
      </section>

      <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]">
        <section className="workspace-panel h-fit min-w-0">
          <h2 className="text-xl font-semibold text-white">Mappings</h2>

          <p className="mt-2 text-sm text-neutral-500">
            Select a canonical skill to inspect and review its candidate.
          </p>

          {loading ? (
            <StatusMessage tone="info">Loading mappings…</StatusMessage>
          ) : queueError ? null : queue?.reviews.length ? (
            <div className="mt-6 space-y-3">
              {queue.reviews.map((review) => (
                <QueueItem
                  key={review.mapping.mapping_id}
                  review={review}
                  selected={
                    selectedReview?.mapping.mapping_id ===
                    review.mapping.mapping_id
                  }
                  onSelect={synchronizeEditor}
                />
              ))}
            </div>
          ) : (
            <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-950/60 p-5">
              <p className="font-medium text-neutral-300">No mappings found</p>

              <p className="mt-2 text-sm leading-6 text-neutral-500">
                There are no mappings matching the selected status.
              </p>
            </div>
          )}
        </section>

        <section className="min-w-0 space-y-6">
          {!selectedReview ? (
            <div className={PANEL_CLASS_NAME}>
              <h2 className="text-xl font-semibold text-white">
                No mapping selected
              </h2>

              <p className="mt-3 text-sm leading-6 text-neutral-500">
                Select a mapping from the review queue to inspect its candidate
                data.
              </p>
            </div>
          ) : (
            <>
              <section className={PANEL_CLASS_NAME}>
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                      Canonical skill
                    </p>

                    <h2 className="mt-2 text-2xl font-semibold text-white">
                      {selectedReview.skill_name}
                    </h2>

                    <p className="mt-2 text-sm text-neutral-500">
                      {selectedReview.domain_name}

                      {selectedReview.category_name
                        ? ` · ${selectedReview.category_name}`
                        : ""}
                    </p>
                  </div>

                  <StatusBadge status={selectedReview.mapping.mapping_status} />
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  <DetailCard
                    label="Coverage"
                    value={
                      selectedReview.mapping.coverage_level
                        ? formatLabel(selectedReview.mapping.coverage_level)
                        : "—"
                    }
                  />

                  <DetailCard
                    label="Relevance"
                    value={formatScore(selectedReview.mapping.relevance_score)}
                  />

                  <DetailCard
                    label="Coverage score"
                    value={formatScore(selectedReview.mapping.coverage_score)}
                  />

                  <DetailCard
                    label="Depth"
                    value={formatScore(selectedReview.mapping.depth_score)}
                  />

                  <DetailCard
                    label="Practicality"
                    value={formatScore(
                      selectedReview.mapping.practicality_score,
                    )}
                  />

                  <DetailCard
                    label="Confidence"
                    value={formatConfidence(selectedReview.mapping.confidence)}
                  />

                  <DetailCard
                    label="Entry level"
                    value={selectedReview.entry_level?.name ?? "—"}
                  />

                  <DetailCard
                    label="Exit level"
                    value={selectedReview.exit_level?.name ?? "—"}
                  />

                  <DetailCard
                    label="Reviewed"
                    value={formatDate(selectedReview.mapping.reviewed_at)}
                  />
                </div>

                {selectedReview.mapping.candidate_error ? (
                  <div className="mt-6 rounded-xl border border-red-900/70 bg-red-950/50 p-4 text-sm text-red-200">
                    {selectedReview.mapping.candidate_error}
                  </div>
                ) : null}
              </section>

              <section className={PANEL_CLASS_NAME}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                      Structured candidate
                    </p>

                    <h2 className="mt-2 text-xl font-semibold text-white">
                      Mapping candidate
                    </h2>

                    <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">
                      Correct the structured mapping when necessary. The backend
                      validates scores, proficiency levels, evidence, and the
                      canonical skill slug.
                    </p>
                  </div>

                  {candidateJson.trim() ? (
                    <span
                      className={
                        candidateIsValid
                          ? "rounded-full border border-emerald-900/70 bg-emerald-950/60 px-3 py-1 text-xs font-medium text-emerald-300"
                          : "rounded-full border border-red-900/70 bg-red-950/60 px-3 py-1 text-xs font-medium text-red-300"
                      }
                    >
                      {candidateIsValid ? "Valid JSON" : "Invalid JSON"}
                    </span>
                  ) : null}
                </div>

                <div className="mt-5">
                  <Field label="Mapping candidate JSON">
                    <textarea
                      value={candidateJson}
                      onChange={(event) => setCandidateJson(event.target.value)}
                      rows={30}
                      spellCheck={false}
                      placeholder="No mapping candidate is available."
                      className={`${FIELD_CLASS_NAME} font-mono text-sm leading-6`}
                    />
                  </Field>
                </div>
              </section>

              <section className={PANEL_CLASS_NAME}>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Trusted evidence
                </p>

                <h2 className="mt-2 text-xl font-semibold text-white">
                  Approved evidence
                </h2>

                <p className="mt-2 text-sm leading-6 text-neutral-400">
                  Evidence appears here only after a mapping has been approved.
                </p>

                {selectedReview.trusted_evidence.length ? (
                  <div className="mt-5 space-y-3">
                    {selectedReview.trusted_evidence.map((evidence) => (
                      <EvidenceCard
                        key={evidence.evidence_id}
                        evidence={evidence}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="mt-5 text-sm text-neutral-500">
                    No trusted evidence has been created.
                  </p>
                )}
              </section>

              <section className={PANEL_CLASS_NAME}>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Human decision
                </p>

                <h2 className="mt-2 text-xl font-semibold text-white">
                  Review notes and approval
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">
                  Approving copies the edited candidate into trusted mapping
                  fields and creates validated evidence records.
                </p>

                <div className="mt-5">
                  <Field label="Review notes">
                    <textarea
                      value={reviewNotes}
                      onChange={(event) => setReviewNotes(event.target.value)}
                      rows={5}
                      placeholder="Record corrections or the reason for your decision."
                      className={`${FIELD_CLASS_NAME} text-sm leading-6`}
                    />
                  </Field>
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={
                      busy || !selectedReview.candidate || !candidateIsValid
                    }
                    onClick={() => void submitReview("approve")}
                    className="workspace-button"
                  >
                    {savingAction === "approve"
                      ? "Approving…"
                      : "Approve mapping"}
                  </button>

                  <button
                    type="button"
                    disabled={busy || !selectedReview.candidate}
                    onClick={() => void submitReview("reject")}
                    className="workspace-button workspace-button--secondary text-red-300"
                  >
                    {savingAction === "reject"
                      ? "Rejecting…"
                      : "Reject mapping"}
                  </button>
                </div>

                {!candidateIsValid && candidateJson.trim() ? (
                  <p className="mt-4 text-sm text-red-300">
                    Correct the candidate JSON before approving this mapping.
                  </p>
                ) : null}
              </section>
            </>
          )}
        </section>
      </div>
    </PageFrame>
  );
}
