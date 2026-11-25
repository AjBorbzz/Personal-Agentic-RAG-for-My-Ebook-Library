"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { ApiError, apiGet, apiRequest } from "@/lib/api";
import { DocumentReviewNav } from "../DocumentReviewNav";

interface ReviewState {
  document_id: string;
  evaluation_status: string;
  evaluation_version: number;

  candidate: Record<string, unknown> | null;

  evaluation_source: string | null;
  evaluation_model: string | null;
  evaluation_error: string | null;
  confidence: number | null;

  evaluated_at: string | null;
  reviewed_at: string | null;
  review_notes: string | null;

  curation: Record<string, unknown>;
}

type ReviewAction = "approve" | "reject";

const PANEL_CLASS_NAME = "workspace-panel min-w-0";
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

function formatConfidence(value: number | null): string {
  if (value === null) {
    return "—";
  }

  const normalized = value <= 1 ? value * 100 : value;

  return `${normalized.toFixed(1)}%`;
}

function isValidJson(value: string): boolean {
  if (!value.trim()) {
    return false;
  }

  try {
    JSON.parse(value);
    return true;
  } catch {
    return false;
  }
}

function StatusBadge({ value }: { value: string }) {
  const normalizedValue = value.toLowerCase();

  let className = "border-neutral-700 bg-neutral-800 text-neutral-300";

  if (normalizedValue === "approved") {
    className = "border-emerald-900/70 bg-emerald-950/60 text-emerald-300";
  } else if (
    normalizedValue === "pending" ||
    normalizedValue === "generating"
  ) {
    className = "border-amber-900/70 bg-amber-950/60 text-amber-300";
  } else if (normalizedValue === "failed" || normalizedValue === "rejected") {
    className = "border-red-900/70 bg-red-950/60 text-red-300";
  }

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${className}`}
    >
      {formatLabel(value)}
    </span>
  );
}

function DetailCard({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
        {label}
      </p>

      <div className="mt-2 min-h-6 text-sm font-medium text-neutral-200">
        {value}
      </div>
    </div>
  );
}

export default function CurationReviewPage() {
  const { documentId } = useParams<{ documentId: string }>();
  return <CurationReview key={documentId} documentId={documentId} />;
}

function CurationReview({ documentId }: { documentId: string }) {
  const curationPath = `/book-curations/${encodeURIComponent(documentId)}`;
  const [revision, setRevision] = useState(0);
  const [notEvaluated, setNotEvaluated] = useState(false);

  const [review, setReview] = useState<ReviewState | null>(null);
  const [candidateJson, setCandidateJson] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [savingAction, setSavingAction] = useState<ReviewAction | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const candidateIsValid = useMemo(
    () => isValidJson(candidateJson),
    [candidateJson],
  );

  const busy = loading || generating || savingAction !== null;

  useEffect(() => {
    const controller = new AbortController();

    apiGet<ReviewState>(`${curationPath}/review`, { signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted) return;

        setNotEvaluated(false);
        setReview(result);
        setCandidateJson(
          result.candidate ? JSON.stringify(result.candidate, null, 2) : "",
        );
        setReviewNotes(result.review_notes ?? "");
      })
      .catch((requestError: unknown) => {
        if (controller.signal.aborted) return;

        if (requestError instanceof ApiError && requestError.status === 404) {
          setNotEvaluated(true);
          setReview(null);
          setCandidateJson("");
          setReviewNotes("");
        } else {
          setNotEvaluated(false);
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load the evaluation.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [curationPath, revision]);

  function refreshReview() {
    setLoading(true);
    setError(null);
    setRevision((current) => current + 1);
  }

  async function generateEvaluation() {
    setGenerating(true);
    setError(null);
    setMessage(null);

    try {
      await apiRequest(`${curationPath}/evaluate`, {
        method: "POST",
        json: { max_source_characters: 12000 },
        responseType: "void",
      });

      setMessage(
        review?.candidate
          ? "The evaluation was regenerated successfully."
          : "The evaluation was generated successfully.",
      );

      refreshReview();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Evaluation generation failed.",
      );
    } finally {
      setGenerating(false);
    }
  }

  async function submitReview(action: ReviewAction) {
    setSavingAction(action);
    setError(null);
    setMessage(null);

    try {
      let editedCandidate: Record<string, unknown> | undefined;

      if (action === "approve") {
        if (!candidateJson.trim()) {
          throw new Error("The evaluation candidate is empty.");
        }

        try {
          editedCandidate = JSON.parse(candidateJson) as Record<
            string,
            unknown
          >;
        } catch {
          throw new Error("The edited candidate is not valid JSON.");
        }
      }

      await apiRequest(`${curationPath}/review`, {
        method: "PATCH",
        json: {
          action,
          edited_candidate: action === "approve" ? editedCandidate : undefined,
          review_notes: reviewNotes.trim() || null,
        },
        responseType: "void",
      });

      setMessage(
        action === "approve"
          ? "The evaluation was approved."
          : "The evaluation was rejected.",
      );

      refreshReview();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The review operation failed.",
      );
    } finally {
      setSavingAction(null);
    }
  }

  return (
    <PageFrame className="space-y-6">
      <PageHeader
        title="Book Evaluation Review"
        description="Inspect the AI-generated evaluation and review the evidence before its scores are used in Book Curator."
        back={{ label: "Book Curator", href: "/book-curator" }}
      >
        <p className="mt-3 break-all font-mono text-xs text-neutral-400">
          Document ID: {documentId}
        </p>
        <DocumentReviewNav documentId={documentId} />
      </PageHeader>

      {loading && (
        <StatusMessage tone="info">Loading book evaluation…</StatusMessage>
      )}
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {message && <StatusMessage tone="success">{message}</StatusMessage>}

      {!loading && !review && !notEvaluated && (
        <div>
          <button
            type="button"
            onClick={refreshReview}
            className={SECONDARY_BUTTON_CLASS_NAME}
          >
            Retry loading evaluation
          </button>
        </div>
      )}

      {notEvaluated && (
        <section className={PANEL_CLASS_NAME}>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
            Evaluation status
          </p>

          <h2 className="mt-3 text-2xl font-semibold text-white">
            This book has not been evaluated
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-neutral-400">
            Generate an AI evaluation to create scores, strengths, weaknesses,
            recommended audience, library role, and priority for human review.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={busy}
              onClick={() => void generateEvaluation()}
              className="workspace-button"
            >
              {generating ? "Generating evaluation…" : "Generate evaluation"}
            </button>
          </div>
        </section>
      )}

      {review && (
        <>
          <section className={PANEL_CLASS_NAME}>
            <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Evaluation status
                </p>

                <div className="mt-3">
                  <StatusBadge value={review.evaluation_status} />
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void generateEvaluation()}
                  className={SECONDARY_BUTTON_CLASS_NAME}
                >
                  {generating
                    ? "Generating…"
                    : review.candidate
                      ? "Regenerate evaluation"
                      : "Generate evaluation"}
                </button>

                <button
                  type="button"
                  disabled={busy}
                  onClick={refreshReview}
                  className={SECONDARY_BUTTON_CLASS_NAME}
                >
                  Refresh
                </button>
              </div>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <DetailCard
                label="Model"
                value={review.evaluation_model ?? "—"}
              />

              <DetailCard
                label="Source"
                value={
                  review.evaluation_source
                    ? formatLabel(review.evaluation_source)
                    : "—"
                }
              />

              <DetailCard label="Version" value={review.evaluation_version} />

              <DetailCard
                label="Confidence"
                value={formatConfidence(review.confidence)}
              />

              <DetailCard
                label="Evaluated"
                value={formatDate(review.evaluated_at)}
              />

              <DetailCard
                label="Reviewed"
                value={formatDate(review.reviewed_at)}
              />
            </div>

            {review.evaluation_error ? (
              <div className="mt-6 rounded-xl border border-red-900/70 bg-red-950/50 p-4 text-sm leading-6 text-red-200">
                <p className="font-semibold">Evaluation error</p>
                <p className="mt-2">{review.evaluation_error}</p>
              </div>
            ) : null}
          </section>

          <section className={PANEL_CLASS_NAME}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Structured evaluation
                </p>

                <h2 className="mt-2 text-xl font-semibold text-white">
                  Evaluation candidate
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">
                  Correct the JSON before approval when necessary. The backend
                  validates the schema and recalculates the overall score.
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
              <Field label="Evaluation candidate JSON">
                <textarea
                  value={candidateJson}
                  onChange={(event) => setCandidateJson(event.target.value)}
                  rows={30}
                  spellCheck={false}
                  placeholder="Generate an evaluation to populate the candidate."
                  className="workspace-field font-mono text-sm leading-6"
                />
              </Field>
            </div>
          </section>

          <section className={PANEL_CLASS_NAME}>
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                Human decision
              </p>

              <h2 className="mt-2 text-xl font-semibold text-white">
                Review notes and approval
              </h2>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">
                Record any corrections, concerns, or reasons for approving or
                rejecting the candidate.
              </p>
            </div>

            <div className="mt-5">
              <Field label="Review notes">
                <textarea
                  value={reviewNotes}
                  onChange={(event) => setReviewNotes(event.target.value)}
                  rows={5}
                  placeholder="Record corrections or the reason for your decision."
                  className="workspace-field text-sm leading-6"
                />
              </Field>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                disabled={busy || !review.candidate || !candidateIsValid}
                onClick={() => void submitReview("approve")}
                className="workspace-button"
              >
                {savingAction === "approve"
                  ? "Approving…"
                  : "Approve evaluation"}
              </button>

              <button
                type="button"
                disabled={busy || !review.candidate}
                onClick={() => void submitReview("reject")}
                className="workspace-button workspace-button--secondary text-red-300"
              >
                {savingAction === "reject" ? "Rejecting…" : "Reject evaluation"}
              </button>
            </div>

            {!candidateIsValid && candidateJson.trim() ? (
              <p className="mt-4 text-sm text-red-300">
                Correct the JSON before approving this evaluation.
              </p>
            ) : null}
          </section>
        </>
      )}
    </PageFrame>
  );
}
