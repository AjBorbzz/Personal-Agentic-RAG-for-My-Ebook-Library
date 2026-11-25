import Link from "next/link";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import type {
  EvaluationResult,
  EvaluationRun,
  EvaluationSource,
} from "@/lib/evaluation-api";

const percentage = new Intl.NumberFormat("en", {
  style: "percent",
  maximumFractionDigits: 1,
});

export function formatRate(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? percentage.format(value)
    : "Not measured";
}

export function formatRunStatus(status: string): string {
  return status
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/^./, (letter) => letter.toUpperCase());
}

function sourcePages({ page_start: start, page_end: end }: EvaluationSource) {
  if (start != null && end != null && start !== end)
    return `Pages ${start}–${end}`;
  if (start != null || end != null) return `Page ${start ?? end}`;
  return "Page not recorded";
}

function SourceList({
  title,
  sources,
}: {
  title: string;
  sources: EvaluationSource[];
}) {
  return (
    <div className="min-w-0">
      <h4 className="font-medium text-neutral-100">{title}</h4>
      {sources.length ? (
        <ul className="mt-2 space-y-2">
          {sources.map((source, index) => {
            const documentId = source.document_id;
            const filename = source.source_file?.split(/[\\/]/).pop();
            const name = filename || documentId || "Unknown document";

            return (
              <li key={`${documentId}-${index}`} className="min-w-0">
                {documentId ? (
                  <Link
                    href={`/documents/${encodeURIComponent(
                      documentId,
                    )}/metadata`}
                    className="break-words underline decoration-neutral-600 underline-offset-4 hover:decoration-current"
                  >
                    {name}
                  </Link>
                ) : (
                  <span className="break-words">{name}</span>
                )}
                <span className="block text-neutral-400">
                  {sourcePages(source)}
                </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="mt-2 text-neutral-400">None recorded.</p>
      )}
    </div>
  );
}

type EvaluationResultsProps = {
  run: EvaluationRun;
  results: EvaluationResult[];
  notes: string;
  onNotesChange: (notes: string) => void;
  onReview: (resultId: string, approved: boolean) => void;
  disabled: boolean;
  reviewingId?: string;
};

export function EvaluationResults({
  run,
  results,
  notes,
  onNotesChange,
  onReview,
  disabled,
  reviewingId,
}: EvaluationResultsProps) {
  const comparison = run.comparison?.decision ?? run.comparison?.status;

  return (
    <section
      className="workspace-panel min-w-0 space-y-4"
      aria-labelledby="evaluation-results"
    >
      <div>
        <h2 id="evaluation-results" className="text-xl font-semibold">
          Run results
        </h2>
        <p className="mt-1 break-words text-sm text-neutral-300">
          {run.dataset_name} / {run.dataset_version}
        </p>
        <p className="mt-1 break-all font-mono text-xs text-neutral-400">
          {run.evaluation_run_id}
        </p>
        <p className="mt-2 text-sm text-neutral-300">
          Baseline comparison{" "}
          {comparison ? formatRunStatus(comparison) : "unavailable"}
        </p>
      </div>
      {run.error_detail && (
        <StatusMessage tone="error">{run.error_detail}</StatusMessage>
      )}
      {results.length ? (
        <Field
          label="Review notes"
          hint="Required for approvals and rejections."
        >
          <textarea
            className="workspace-field"
            value={notes}
            onChange={(event) => onNotesChange(event.target.value)}
            rows={2}
            maxLength={4000}
          />
        </Field>
      ) : (
        <StatusMessage tone="info">
          This run has no recorded case results.
        </StatusMessage>
      )}
      {results.map((result) => {
        const pending =
          result.human_groundedness == null ||
          result.human_relevance == null ||
          result.human_completeness == null;
        const status = result.passed
          ? "Passed"
          : pending
            ? "Pending review"
            : "Needs attention";
        const reviewing = reviewingId === result.evaluation_result_id;

        return (
          <article
            key={result.evaluation_result_id}
            className="min-w-0 space-y-3 rounded-xl border border-neutral-800 bg-neutral-950 p-4"
            aria-busy={reviewing}
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="min-w-0 break-words text-sm font-medium text-neutral-200">
                Case{" "}
                <span className="break-all font-mono text-xs text-neutral-400">
                  {result.evaluation_case_id}
                </span>
              </h3>
              <span className="workspace-badge">{status}</span>
            </div>
            <p className="break-words text-sm text-neutral-300">
              Failures{" "}
              {result.failure_categories.length
                ? result.failure_categories.map(formatRunStatus).join(", ")
                : "not detected"}
            </p>
            {result.answer ? (
              <details className="text-sm text-neutral-300">
                <summary className="cursor-pointer font-medium text-neutral-100">
                  Generated answer
                </summary>
                <p className="mt-2 whitespace-pre-wrap break-words">
                  {result.answer}
                </p>
              </details>
            ) : (
              <p className="text-sm text-neutral-400">
                No answer was recorded.
              </p>
            )}
            <details className="text-sm text-neutral-300">
              <summary className="cursor-pointer font-medium text-neutral-100">
                Retrieved sources and citations
              </summary>
              <div className="mt-3 grid gap-4 sm:grid-cols-2">
                <SourceList
                  title="Retrieved sources"
                  sources={result.retrieved_sources ?? []}
                />
                <SourceList
                  title="Cited sources"
                  sources={result.citations ?? []}
                />
              </div>
            </details>
            <details className="text-sm text-neutral-300">
              <summary className="cursor-pointer font-medium text-neutral-100">
                Case metrics
              </summary>
              <pre className="mt-2 overflow-x-auto rounded-md bg-neutral-900 p-3 text-xs text-neutral-400">
                {JSON.stringify(result.metrics, null, 2)}
              </pre>
            </details>
            {result.error_detail && (
              <StatusMessage tone="error">{result.error_detail}</StatusMessage>
            )}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="workspace-button"
                disabled={disabled || !notes.trim()}
                onClick={() => onReview(result.evaluation_result_id, true)}
              >
                Approve answer
              </button>
              <button
                type="button"
                className="workspace-button workspace-button--secondary"
                disabled={disabled || !notes.trim()}
                onClick={() => onReview(result.evaluation_result_id, false)}
              >
                Reject answer
              </button>
            </div>
            <p className="text-sm text-neutral-400">
              Review covers groundedness, relevance, and completeness.
            </p>
          </article>
        );
      })}
    </section>
  );
}
