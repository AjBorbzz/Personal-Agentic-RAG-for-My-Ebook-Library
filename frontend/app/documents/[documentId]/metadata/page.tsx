"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { DocumentReviewNav } from "../DocumentReviewNav";
import {
  CandidateMetadata,
  QdrantStatus,
  ReviewStatusBadge,
  TrustedMetadata,
} from "./MetadataSections";
import {
  EMPTY_CANDIDATE,
  type EnrichedBookMetadata,
  type MetadataCandidateResponse,
  type MetadataReviewResponse,
  type MetadataReviewState,
  type QdrantSyncResponse,
  type ReviewRequest,
  type StageCandidateRequest,
  type SyncRequest,
} from "./metadata-types";

export default function MetadataEditorPage() {
  const { documentId } = useParams<{ documentId: string }>();
  return <MetadataEditor key={documentId} documentId={documentId} />;
}

function MetadataEditor({ documentId }: { documentId: string }) {
  const [reviewState, setReviewState] = useState<MetadataReviewState | null>(
    null,
  );

  const [candidate, setCandidate] =
    useState<EnrichedBookMetadata>(EMPTY_CANDIDATE);

  const [overwriteExisting, setOverwriteExisting] = useState(false);

  const [syncToQdrant, setSyncToQdrant] = useState(true);

  const [maxSourceCharacters, setMaxSourceCharacters] = useState(24000);

  const [reviewNotes, setReviewNotes] = useState("");

  const [loading, setLoading] = useState(true);

  const [generating, setGenerating] = useState(false);

  const [reviewing, setReviewing] = useState(false);

  const [syncing, setSyncing] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [message, setMessage] = useState<string | null>(null);

  const [warnings, setWarnings] = useState<string[]>([]);

  const [syncResult, setSyncResult] = useState<QdrantSyncResponse | null>(null);

  const [revision, setRevision] = useState(0);
  const [loadedRevision, setLoadedRevision] = useState(0);
  const documentPath = `/documents/${encodeURIComponent(documentId)}`;

  useEffect(() => {
    const controller = new AbortController();

    apiGet<MetadataReviewState>(`${documentPath}/metadata-review`, {
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted) return;

        setLoadedRevision(revision);
        setReviewState(data);
        setReviewNotes(data.review_notes ?? "");
        setCandidate(data.candidate ?? EMPTY_CANDIDATE);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load metadata review.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [documentPath, revision]);

  function refreshReview() {
    setLoading(true);
    setRevision((current) => current + 1);
  }

  const document = reviewState?.document ?? null;

  const candidateChanged = useMemo(() => {
    if (!reviewState?.candidate) {
      return false;
    }

    return JSON.stringify(candidate) !== JSON.stringify(reviewState.candidate);
  }, [candidate, reviewState]);

  function updateCandidate<K extends keyof EnrichedBookMetadata>(
    field: K,
    value: EnrichedBookMetadata[K],
  ) {
    setCandidate((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function generateCandidate() {
    if (maxSourceCharacters < 4000 || maxSourceCharacters > 60000) {
      setError("Use a source character limit between 4,000 and 60,000.");
      setMessage(null);
      return;
    }

    setGenerating(true);
    setError(null);
    setMessage(null);
    setWarnings([]);
    setSyncResult(null);

    try {
      const response = await apiPost<
        MetadataCandidateResponse,
        StageCandidateRequest
      >(`${documentPath}/metadata-candidate`, {
        overwrite_existing: overwriteExisting,
        max_source_characters: maxSourceCharacters,
      });

      setCandidate(response.candidate);
      setWarnings(response.warnings);
      setMessage("Metadata candidate generated and staged for review.");

      refreshReview();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate metadata candidate.",
      );
    } finally {
      setGenerating(false);
    }
  }

  async function approveCandidate() {
    const confirmed = window.confirm(
      "Approve this metadata candidate and apply it to the document?",
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
      const response = await apiPatch<MetadataReviewResponse, ReviewRequest>(
        `${documentPath}/metadata-review`,
        {
          action: "approve",
          overwrite_existing: overwriteExisting,
          sync_to_qdrant: syncToQdrant,
          review_notes: reviewNotes.trim() || null,
          edited_candidate: candidate,
        },
      );

      setWarnings(response.warnings || []);
      setSyncResult(response.qdrant_sync);

      setMessage(
        response.applied
          ? `Metadata approved. Updated fields: ${response.updated_fields.join(
              ", ",
            )}`
          : "Metadata approved, but no document fields required changes.",
      );

      refreshReview();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to approve metadata.",
      );
    } finally {
      setReviewing(false);
    }
  }

  async function rejectCandidate() {
    const confirmed = window.confirm("Reject this metadata candidate?");

    if (!confirmed) {
      return;
    }

    setReviewing(true);
    setError(null);
    setMessage(null);
    setWarnings([]);
    setSyncResult(null);

    try {
      const response = await apiPatch<MetadataReviewResponse, ReviewRequest>(
        `${documentPath}/metadata-review`,
        {
          action: "reject",
          overwrite_existing: false,
          sync_to_qdrant: false,
          review_notes: reviewNotes.trim() || null,
        },
      );

      setMessage(`Metadata candidate ${response.review_status}.`);

      refreshReview();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to reject metadata.",
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
      const response = await apiPost<QdrantSyncResponse, SyncRequest>(
        `${documentPath}/sync-qdrant`,
        {
          force: false,
          create_payload_indexes: true,
        },
      );

      setSyncResult(response);
      setWarnings(response.warnings || []);

      setMessage(
        `Synchronized metadata to ${response.matched_points} Qdrant chunk(s).`,
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to synchronize Qdrant.",
      );
    } finally {
      setSyncing(false);
    }
  }

  const busy = loading || generating || reviewing || syncing;

  return (
    <PageFrame width="wide" className="space-y-6">
      <PageHeader
        title="Metadata Review"
        description={
          document?.title ||
          document?.filename ||
          "Review the indexed edition and approve corrected ebook metadata."
        }
        back={{ label: "Document Library", href: "/documents" }}
        actions={
          reviewState && (
            <button
              type="button"
              onClick={generateCandidate}
              disabled={busy}
              className="workspace-button"
            >
              {generating
                ? "Generating…"
                : reviewState.candidate
                  ? "Regenerate candidate"
                  : "Generate candidate"}
            </button>
          )
        }
      >
        {reviewState && document && (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <ReviewStatusBadge status={reviewState.review_status} />
            <p className="min-w-0 font-mono text-xs text-neutral-400 [overflow-wrap:anywhere]">
              {document.document_id}
            </p>
          </div>
        )}
        <DocumentReviewNav documentId={documentId} />
      </PageHeader>

      {loading && (
        <StatusMessage tone="info">Loading metadata review…</StatusMessage>
      )}
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {message && <StatusMessage tone="success">{message}</StatusMessage>}

      {warnings.length > 0 && (
        <StatusMessage tone="info">
          <p className="font-medium">Warnings</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </StatusMessage>
      )}

      {reviewState && document && (
        <>
          <section className="workspace-panel" aria-busy={loading}>
            <h2 className="text-xl font-semibold">Generation settings</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <label className="workspace-field flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={overwriteExisting}
                  onChange={(event) =>
                    setOverwriteExisting(event.target.checked)
                  }
                />
                Allow approved metadata to overwrite existing values
              </label>
              <label className="workspace-field flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={syncToQdrant}
                  onChange={(event) => setSyncToQdrant(event.target.checked)}
                />
                Synchronize to Qdrant after approval
              </label>
              <Field label="Source character limit">
                <input
                  type="number"
                  min={4000}
                  max={60000}
                  step={1000}
                  value={maxSourceCharacters || ""}
                  onChange={(event) =>
                    setMaxSourceCharacters(Number(event.target.value))
                  }
                  className="workspace-field"
                />
              </Field>
            </div>
          </section>

          <div className="grid min-w-0 gap-6 lg:grid-cols-2">
            <TrustedMetadata document={document} />
            <CandidateMetadata
              key={loadedRevision}
              candidate={reviewState.candidate ? candidate : null}
              edited={candidateChanged}
              onChange={updateCandidate}
            />
          </div>

          {reviewState.candidate && (
            <section className="workspace-panel">
              <h2 className="text-xl font-semibold">Review decision</h2>
              <div className="mt-5">
                <Field label="Review notes">
                  <textarea
                    rows={4}
                    value={reviewNotes}
                    onChange={(event) => setReviewNotes(event.target.value)}
                    placeholder="Describe corrections, concerns, or approval reasoning."
                    className="workspace-field"
                  />
                </Field>
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={approveCandidate}
                  disabled={busy}
                  className="workspace-button"
                >
                  {reviewing ? "Processing…" : "Approve metadata"}
                </button>
                <button
                  type="button"
                  onClick={rejectCandidate}
                  disabled={busy}
                  className="workspace-button workspace-button--secondary text-red-300"
                >
                  Reject candidate
                </button>
              </div>
            </section>
          )}

          {reviewState.review_status === "approved" && (
            <QdrantStatus
              busy={busy}
              syncing={syncing}
              result={syncResult}
              onSync={synchronizeQdrant}
            />
          )}

          <section className="workspace-panel min-w-0">
            <h2 className="text-xl font-semibold">Proposed updates</h2>
            <pre className="mt-4 overflow-auto whitespace-pre-wrap rounded-xl border border-neutral-800 bg-neutral-950 p-4 text-xs text-neutral-400 [overflow-wrap:anywhere]">
              {JSON.stringify(reviewState.proposed_updates, null, 2)}
            </pre>
          </section>
        </>
      )}
    </PageFrame>
  );
}
