"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

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

const PANEL_CLASS_NAME =
  "rounded-2xl border border-neutral-800 bg-neutral-900 p-6";

const FIELD_CLASS_NAME =
  "w-full rounded-xl border border-neutral-700 bg-neutral-950 p-4 " +
  "text-neutral-100 outline-none transition placeholder:text-neutral-600 " +
  "focus:border-neutral-500 focus:ring-2 focus:ring-neutral-800";

const SECONDARY_BUTTON_CLASS_NAME =
  "rounded-xl border border-neutral-700 px-4 py-2.5 text-sm font-medium " +
  "text-neutral-200 transition hover:border-neutral-600 hover:bg-neutral-800 " +
  "disabled:cursor-not-allowed disabled:opacity-50";

async function apiError(
  response: Response,
): Promise<string> {
  try {
    const body: unknown = await response.json();

    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body
    ) {
      const detail = (
        body as { detail?: unknown }
      ).detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (detail !== undefined) {
        return JSON.stringify(detail);
      }
    }

    return JSON.stringify(body);
  } catch {
    return `Request failed with status ${response.status}.`;
  }
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatConfidence(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  const normalized =
    value <= 1 ? value * 100 : value;

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

function StatusBadge({
  value,
}: {
  value: string;
}) {
  const normalizedValue = value.toLowerCase();

  let className =
    "border-neutral-700 bg-neutral-800 text-neutral-300";

  if (normalizedValue === "approved") {
    className =
      "border-emerald-900/70 bg-emerald-950/60 text-emerald-300";
  } else if (
    normalizedValue === "pending" ||
    normalizedValue === "generating"
  ) {
    className =
      "border-amber-900/70 bg-amber-950/60 text-amber-300";
  } else if (
    normalizedValue === "failed" ||
    normalizedValue === "rejected"
  ) {
    className =
      "border-red-900/70 bg-red-950/60 text-red-300";
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
  const parameters = useParams<{
    documentId: string;
  }>();

  const documentId = parameters.documentId;

  const [review, setReview] =
    useState<ReviewState | null>(null);
  const [candidateJson, setCandidateJson] =
    useState("");
  const [reviewNotes, setReviewNotes] =
    useState("");

  const [loading, setLoading] =
    useState(true);
  const [generating, setGenerating] =
    useState(false);
  const [savingAction, setSavingAction] =
    useState<ReviewAction | null>(null);

  const [error, setError] =
    useState<string | null>(null);
  const [message, setMessage] =
    useState<string | null>(null);

  const candidateIsValid = useMemo(
    () => isValidJson(candidateJson),
    [candidateJson],
  );

  const busy =
    loading ||
    generating ||
    savingAction !== null;

  const loadReview = useCallback(
    async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/book-curations/` +
            `${documentId}/review`,
          {
            cache: "no-store",
          },
        );

        if (response.status === 404) {
          setReview(null);
          setCandidateJson("");
          setReviewNotes("");
          return;
        }

        if (!response.ok) {
          throw new Error(
            await apiError(response),
          );
        }

        const result =
          (await response.json()) as ReviewState;

        setReview(result);
        setCandidateJson(
          result.candidate
            ? JSON.stringify(
                result.candidate,
                null,
                2,
              )
            : "",
        );
        setReviewNotes(
          result.review_notes ?? "",
        );
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load the evaluation.",
        );
      } finally {
        setLoading(false);
      }
    },
    [documentId],
  );

  useEffect(() => {
    void loadReview();
  }, [loadReview]);

  async function generateEvaluation() {
    setGenerating(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/book-curations/` +
          `${documentId}/evaluate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            max_source_characters: 12000,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          await apiError(response),
        );
      }

      setMessage(
        review?.candidate
          ? "The evaluation was regenerated successfully."
          : "The evaluation was generated successfully.",
      );

      await loadReview();
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

  async function submitReview(
    action: ReviewAction,
  ) {
    setSavingAction(action);
    setError(null);
    setMessage(null);

    try {
      let editedCandidate:
        | Record<string, unknown>
        | undefined;

      if (action === "approve") {
        if (!candidateJson.trim()) {
          throw new Error(
            "The evaluation candidate is empty.",
          );
        }

        try {
          editedCandidate = JSON.parse(
            candidateJson,
          ) as Record<string, unknown>;
        } catch {
          throw new Error(
            "The edited candidate is not valid JSON.",
          );
        }
      }

      const response = await fetch(
        `${API_BASE_URL}/book-curations/` +
          `${documentId}/review`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            action,
            edited_candidate:
              action === "approve"
                ? editedCandidate
                : undefined,
            review_notes:
              reviewNotes.trim() || null,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          await apiError(response),
        );
      }

      setMessage(
        action === "approve"
          ? "The evaluation was approved."
          : "The evaluation was rejected.",
      );

      await loadReview();
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

  if (loading && !review) {
    return (
      <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
        <section className="mx-auto max-w-5xl">
          <Link
            href="/book-curator"
            className="text-sm font-medium text-blue-400 transition hover:text-blue-300 hover:underline"
          >
            ← Back to Book Curator
          </Link>

          <div className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-8 text-neutral-400">
            Loading book evaluation…
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-5xl space-y-8">
        <header>
          <Link
            href="/book-curator"
            className="text-sm font-medium text-blue-400 transition hover:text-blue-300 hover:underline"
          >
            ← Back to Book Curator
          </Link>

          <p className="mt-8 text-sm font-medium uppercase tracking-[0.3em] text-neutral-500">
            Library Intelligence
          </p>

          <h1 className="mt-4 text-4xl font-bold tracking-tight text-white md:text-5xl">
            Book Evaluation Review
          </h1>

          <p className="mt-5 max-w-3xl text-lg leading-8 text-neutral-400">
            Inspect the AI-generated evaluation,
            correct its structured fields, and
            approve or reject it before the scores
            become trusted curator data.
          </p>

          <p className="mt-4 break-all font-mono text-xs text-neutral-600">
            Document ID: {documentId}
          </p>
        </header>

        {error ? (
          <div
            role="alert"
            className="rounded-2xl border border-red-900/70 bg-red-950/50 p-5 text-red-200"
          >
            <p className="font-semibold">
              Operation failed
            </p>
            <p className="mt-2 text-sm leading-6">
              {error}
            </p>
          </div>
        ) : null}

        {message ? (
          <div
            role="status"
            className="rounded-2xl border border-emerald-900/70 bg-emerald-950/50 p-5 text-emerald-200"
          >
            {message}
          </div>
        ) : null}

        {!review ? (
          <section className={PANEL_CLASS_NAME}>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
              Evaluation status
            </p>

            <h2 className="mt-3 text-2xl font-semibold text-white">
              This book has not been evaluated
            </h2>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-neutral-400">
              Generate an AI evaluation to create
              scores, strengths, weaknesses,
              recommended audience, library role,
              and priority for human review.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void generateEvaluation()
                }
                className="rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {generating
                  ? "Generating evaluation…"
                  : "Generate evaluation"}
              </button>

              <Link
                href={`/documents/${documentId}/metadata`}
                className={SECONDARY_BUTTON_CLASS_NAME}
              >
                Review metadata
              </Link>
              
            </div>
          </section>
        ) : (
          <>
            <section className={PANEL_CLASS_NAME}>
              <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                    Evaluation status
                  </p>

                  <div className="mt-3">
                    <StatusBadge
                      value={
                        review.evaluation_status
                      }
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void generateEvaluation()
                    }
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
                    onClick={() =>
                      void loadReview()
                    }
                    className={SECONDARY_BUTTON_CLASS_NAME}
                  >
                    Refresh
                  </button>

                  <Link
                    href={`/documents/${documentId}/metadata`}
                    className={SECONDARY_BUTTON_CLASS_NAME}
                  >
                    Review metadata
                  </Link>
                </div>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <DetailCard
                  label="Model"
                  value={
                    review.evaluation_model ?? "—"
                  }
                />

                <DetailCard
                  label="Source"
                  value={
                    review.evaluation_source
                      ? formatLabel(
                          review.evaluation_source,
                        )
                      : "—"
                  }
                />

                <DetailCard
                  label="Version"
                  value={
                    review.evaluation_version
                  }
                />

                <DetailCard
                  label="Confidence"
                  value={formatConfidence(
                    review.confidence,
                  )}
                />

                <DetailCard
                  label="Evaluated"
                  value={formatDate(
                    review.evaluated_at,
                  )}
                />

                <DetailCard
                  label="Reviewed"
                  value={formatDate(
                    review.reviewed_at,
                  )}
                />
              </div>

              {review.evaluation_error ? (
                <div className="mt-6 rounded-xl border border-red-900/70 bg-red-950/50 p-4 text-sm leading-6 text-red-200">
                  <p className="font-semibold">
                    Evaluation error
                  </p>
                  <p className="mt-2">
                    {review.evaluation_error}
                  </p>
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
                    Correct the JSON before approval
                    when necessary. The backend
                    validates the schema and
                    recalculates the overall score.
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
                    {candidateIsValid
                      ? "Valid JSON"
                      : "Invalid JSON"}
                  </span>
                ) : null}
              </div>

              <textarea
                value={candidateJson}
                onChange={(event) =>
                  setCandidateJson(
                    event.target.value,
                  )
                }
                rows={30}
                spellCheck={false}
                aria-label="Evaluation candidate JSON"
                placeholder="Generate an evaluation to populate the candidate."
                className={`${FIELD_CLASS_NAME} mt-5 font-mono text-sm leading-6`}
              />
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
                  Record any corrections, concerns,
                  or reasons for approving or
                  rejecting the candidate.
                </p>
              </div>

              <textarea
                value={reviewNotes}
                onChange={(event) =>
                  setReviewNotes(
                    event.target.value,
                  )
                }
                rows={5}
                placeholder="Record corrections or the reason for your decision."
                className={`${FIELD_CLASS_NAME} mt-5 text-sm leading-6`}
              />

              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={
                    busy ||
                    !review.candidate ||
                    !candidateIsValid
                  }
                  onClick={() =>
                    void submitReview("approve")
                  }
                  className="rounded-xl bg-white px-5 py-2.5 text-sm font-medium text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {savingAction === "approve"
                    ? "Approving…"
                    : "Approve evaluation"}
                </button>

                <button
                  type="button"
                  disabled={
                    busy || !review.candidate
                  }
                  onClick={() =>
                    void submitReview("reject")
                  }
                  className="rounded-xl border border-red-900/70 px-5 py-2.5 text-sm font-medium text-red-300 transition hover:bg-red-950/50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {savingAction === "reject"
                    ? "Rejecting…"
                    : "Reject evaluation"}
                </button>
              </div>

              {!candidateIsValid &&
              candidateJson.trim() ? (
                <p className="mt-4 text-sm text-red-300">
                  Correct the JSON before approving
                  this evaluation.
                </p>
              ) : null}
            </section>
          </>
        )}
      </section>
    </main>
  );
}