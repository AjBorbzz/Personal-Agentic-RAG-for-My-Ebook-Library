"use client";

import Link from "next/link";
import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  fetchBookCuratorDashboard,
  reviewRelationship,
} from "@/lib/book-curator-api";

import type {
  BookCuratorDashboard,
  BookRelationship,
  RankingPurpose,
} from "@/lib/book-curator-types";

const PURPOSE_OPTIONS: Array<{
  value: RankingPurpose;
  label: string;
}> = [
  {
    value: "general",
    label: "General quality",
  },
  {
    value: "learning",
    label: "Learning",
  },
  {
    value: "project",
    label: "Project implementation",
  },
  {
    value: "reference",
    label: "Technical reference",
  },
  {
    value: "current_technology",
    label: "Current technology",
  },
  {
    value: "foundational",
    label: "Foundational",
  },
];

const FIELD_CLASS_NAME =
  "w-full rounded-xl border border-neutral-700 bg-neutral-950 px-3 py-2.5 " +
  "text-neutral-100 outline-none transition placeholder:text-neutral-600 " +
  "focus:border-neutral-500 focus:ring-2 focus:ring-neutral-800";

const SECONDARY_BUTTON_CLASS_NAME =
  "rounded-xl border border-neutral-700 px-4 py-2 text-sm font-medium " +
  "text-neutral-200 transition hover:border-neutral-600 hover:bg-neutral-800 " +
  "disabled:cursor-not-allowed disabled:opacity-50";

function displayBookName(
  title: string | null,
  filename: string | null,
): string {
  return title ?? filename ?? "Untitled document";
}

function relationshipDocumentLabel(
  snapshot: Record<string, unknown> | null,
  documentId: string,
): string {
  if (!snapshot) {
    return documentId;
  }

  const title = snapshot.title;
  const filename = snapshot.filename;

  if (typeof title === "string" && title.trim()) {
    return title;
  }

  if (typeof filename === "string" && filename.trim()) {
    return filename;
  }

  return documentId;
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function StatCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description?: string;
}) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
        {label}
      </p>

      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>

      {description ? (
        <p className="mt-2 text-sm leading-6 text-neutral-500">
          {description}
        </p>
      ) : null}
    </div>
  );
}

function StatusBadge({
  value,
}: {
  value: string;
}) {
  const normalizedValue = value.toLowerCase();

  let badgeClassName =
    "border-neutral-700 bg-neutral-800 text-neutral-300";

  if (
    normalizedValue === "approved" ||
    normalizedValue === "top_pick" ||
    normalizedValue === "essential"
  ) {
    badgeClassName =
      "border-emerald-900/70 bg-emerald-950/60 text-emerald-300";
  } else if (
    normalizedValue === "pending" ||
    normalizedValue === "generating"
  ) {
    badgeClassName =
      "border-amber-900/70 bg-amber-950/60 text-amber-300";
  } else if (
    normalizedValue === "failed" ||
    normalizedValue === "rejected" ||
    normalizedValue === "archive_or_avoid"
  ) {
    badgeClassName =
      "border-red-900/70 bg-red-950/60 text-red-300";
  } else if (
    normalizedValue === "recommended" ||
    normalizedValue === "high"
  ) {
    badgeClassName =
      "border-blue-900/70 bg-blue-950/60 text-blue-300";
  }

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${badgeClassName}`}
    >
      {formatLabel(value)}
    </span>
  );
}

export default function BookCuratorPage() {
  const [purpose, setPurpose] =
    useState<RankingPurpose>("general");
  const [audienceLevel, setAudienceLevel] =
    useState("");
  const [domain, setDomain] = useState("");
  const [topic, setTopic] = useState("");
  const [technology, setTechnology] =
    useState("");

  const [dashboard, setDashboard] =
    useState<BookCuratorDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] =
    useState<string | null>(null);
  const [
    relationshipActionId,
    setRelationshipActionId,
  ] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result =
        await fetchBookCuratorDashboard({
          purpose,
          domain,
          topic,
          technology,
          audienceLevel,
        });

      setDashboard(result);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load the Book Curator dashboard.",
      );
    } finally {
      setLoading(false);
    }
  }, [
    purpose,
    domain,
    topic,
    technology,
    audienceLevel,
  ]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  function handleFilterSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    void loadDashboard();
  }

  function clearFilters() {
    setPurpose("general");
    setAudienceLevel("");
    setDomain("");
    setTopic("");
    setTechnology("");
  }

  async function handleRelationshipAction(
    relationship: BookRelationship,
    action: "approve" | "reject",
  ) {
    setRelationshipActionId(
      relationship.relationship_id,
    );
    setError(null);

    try {
      await reviewRelationship(
        relationship.relationship_id,
        action,
      );

      await loadDashboard();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Relationship review failed.",
      );
    } finally {
      setRelationshipActionId(null);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-7xl space-y-8">
        <header>
          <Link
            href="/"
            className="text-sm font-medium text-blue-400 transition hover:text-blue-300 hover:underline"
          >
            ← Back to tools
          </Link>

          <p className="mt-8 text-sm font-medium uppercase tracking-[0.3em] text-neutral-500">
            Library Intelligence
          </p>

          <h1 className="mt-4 max-w-4xl text-4xl font-bold tracking-tight text-white md:text-5xl">
            Book Curator
          </h1>

          <p className="mt-5 max-w-3xl text-lg leading-8 text-neutral-400">
            Evaluate book quality, rank your strongest
            sources, and resolve duplicate, overlapping,
            or superseded editions in your ebook library.
          </p>
        </header>

        <form
          onSubmit={handleFilterSubmit}
          className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6"
        >
          <div>
            <h2 className="text-xl font-semibold text-white">
              Recommendation filters
            </h2>

            <p className="mt-2 text-sm leading-6 text-neutral-400">
              Rank books for a learning goal, technical
              domain, audience level, topic, or technology.
            </p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <label className="space-y-2">
              <span className="text-sm font-medium text-neutral-300">
                Ranking purpose
              </span>

              <select
                value={purpose}
                onChange={(event) =>
                  setPurpose(
                    event.target.value as RankingPurpose,
                  )
                }
                className={FIELD_CLASS_NAME}
              >
                {PURPOSE_OPTIONS.map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-neutral-300">
                Audience
              </span>

              <select
                value={audienceLevel}
                onChange={(event) =>
                  setAudienceLevel(event.target.value)
                }
                className={FIELD_CLASS_NAME}
              >
                <option value="">Any audience</option>
                <option value="beginner">
                  Beginner
                </option>
                <option value="intermediate">
                  Intermediate
                </option>
                <option value="advanced">
                  Advanced
                </option>
                <option value="mixed">Mixed</option>
              </select>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-neutral-300">
                Domain
              </span>

              <input
                value={domain}
                onChange={(event) =>
                  setDomain(event.target.value)
                }
                placeholder="cybersecurity"
                className={FIELD_CLASS_NAME}
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-neutral-300">
                Topic
              </span>

              <input
                value={topic}
                onChange={(event) =>
                  setTopic(event.target.value)
                }
                placeholder="backend architecture"
                className={FIELD_CLASS_NAME}
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-neutral-300">
                Technology
              </span>

              <input
                value={technology}
                onChange={(event) =>
                  setTechnology(event.target.value)
                }
                placeholder="fastapi"
                className={FIELD_CLASS_NAME}
              />
            </label>

            <div className="flex items-end gap-3">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading
                  ? "Refreshing…"
                  : "Refresh dashboard"}
              </button>

              <button
                type="button"
                onClick={clearFilters}
                disabled={loading}
                className={SECONDARY_BUTTON_CLASS_NAME}
              >
                Clear
              </button>
            </div>
          </div>
        </form>

        {error ? (
          <div
            role="alert"
            className="rounded-2xl border border-red-900/70 bg-red-950/50 p-5 text-sm text-red-200"
          >
            <p className="font-semibold">
              Unable to load Book Curator
            </p>
            <p className="mt-2 leading-6">{error}</p>
          </div>
        ) : null}

        {loading && !dashboard ? (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-8 text-neutral-400">
            Loading Book Curator…
          </div>
        ) : null}

        {dashboard ? (
          <>
            {dashboard.warnings.length ? (
              <section className="rounded-2xl border border-amber-900/60 bg-amber-950/30 p-5">
                <h2 className="font-semibold text-amber-200">
                  Dashboard notices
                </h2>

                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-amber-300/90">
                  {dashboard.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </section>
            ) : null}

            <section>
              <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                    Overview
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold text-white">
                    Library status
                  </h2>
                </div>

                <p className="text-sm text-neutral-500">
                  Updated{" "}
                  {new Date(
                    dashboard.generated_at,
                  ).toLocaleString()}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard
                  label="Total documents"
                  value={
                    dashboard.stats.total_documents
                  }
                />

                <StatCard
                  label="Approved evaluations"
                  value={
                    dashboard.stats
                      .approved_evaluations
                  }
                />

                <StatCard
                  label="Pending evaluations"
                  value={
                    dashboard.stats
                      .pending_evaluations
                  }
                />

                <StatCard
                  label="Not evaluated"
                  value={
                    dashboard.stats.not_evaluated
                  }
                />

                <StatCard
                  label="Essential books"
                  value={
                    dashboard.stats.essential_books
                  }
                />

                <StatCard
                  label="Top picks"
                  value={
                    dashboard.stats.top_pick_books
                  }
                />

                <StatCard
                  label="Pending relationships"
                  value={
                    dashboard.stats
                      .pending_relationships
                  }
                />

                <StatCard
                  label="Different editions"
                  value={
                    dashboard.stats
                      .different_editions
                  }
                />
              </div>
            </section>

            <section className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900">
              <div className="border-b border-neutral-800 p-6">
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Recommendations
                </p>

                <h2 className="mt-2 text-xl font-semibold text-white">
                  Ranked books
                </h2>

                <p className="mt-2 text-sm text-neutral-400">
                  Approved books ranked for{" "}
                  {purpose.replaceAll("_", " ")}.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-800">
                  <thead className="bg-neutral-950/60">
                    <tr>
                      {[
                        "Book",
                        "Score",
                        "Tier",
                        "Role",
                        "Priority",
                        "Actions",
                      ].map((heading) => (
                        <th
                          key={heading}
                          className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wide text-neutral-500"
                        >
                          {heading}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-neutral-800">
                    {dashboard.top_books.map((book) => (
                      <tr
                        key={book.document_id}
                        className="transition hover:bg-neutral-800/40"
                      >
                        <td className="min-w-72 px-5 py-4">
                          <p className="font-medium text-white">
                            {displayBookName(
                              book.title,
                              book.filename,
                            )}
                          </p>

                          <p className="mt-1 text-sm text-neutral-500">
                            {book.author ??
                              "Unknown author"}
                            {book.publication_year
                              ? ` · ${book.publication_year}`
                              : ""}
                          </p>
                        </td>

                        <td className="px-5 py-4">
                          <span className="text-lg font-semibold text-white">
                            {book.ranking_score.toFixed(
                              1,
                            )}
                          </span>
                          <span className="text-sm text-neutral-600">
                            /100
                          </span>
                        </td>

                        <td className="px-5 py-4">
                          <StatusBadge
                            value={
                              book.recommendation_tier
                            }
                          />
                        </td>

                        <td className="px-5 py-4 text-sm text-neutral-300">
                          {book.recommended_role
                            ? formatLabel(
                                book.recommended_role,
                              )
                            : "—"}
                        </td>

                        <td className="px-5 py-4">
                          {book.library_priority ? (
                            <StatusBadge
                              value={
                                book.library_priority
                              }
                            />
                          ) : (
                            <span className="text-neutral-500">
                              —
                            </span>
                          )}
                        </td>

                        <td className="px-5 py-4">
                          <div className="flex flex-wrap gap-3">
                            <Link
                              href={`/documents/${book.document_id}/curation`}
                              className="text-sm font-medium text-blue-400 transition hover:text-blue-300 hover:underline"
                            >
                              Curation
                            </Link>

                            <Link
                              href={`/documents/${book.document_id}/metadata`}
                              className="text-sm font-medium text-blue-400 transition hover:text-blue-300 hover:underline"
                            >
                              Metadata
                            </Link>
                          </div>
                        </td>
                      </tr>
                    ))}

                    {!dashboard.top_books.length ? (
                      <tr>
                        <td
                          colSpan={6}
                          className="px-5 py-12 text-center text-neutral-500"
                        >
                          No approved ranked books
                          match the current filters.
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900">
              <div className="border-b border-neutral-800 p-6">
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Human review
                </p>

                <h2 className="mt-2 text-xl font-semibold text-white">
                  Evaluation queue
                </h2>

                <p className="mt-2 text-sm text-neutral-400">
                  Review pending, failed, or
                  in-progress AI evaluations.
                </p>
              </div>

              <div className="divide-y divide-neutral-800">
                {dashboard.review_queue.map(
                  (item) => (
                    <article
                      key={item.document_id}
                      className="flex flex-col gap-4 p-6 transition hover:bg-neutral-800/30 md:flex-row md:items-center md:justify-between"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium text-white">
                          {displayBookName(
                            item.title,
                            item.filename,
                          )}
                        </p>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <StatusBadge
                            value={
                              item.evaluation_status
                            }
                          />

                          {item.evaluation_model ? (
                            <span className="text-sm text-neutral-500">
                              {item.evaluation_model}
                            </span>
                          ) : null}

                          {item.publication_year ? (
                            <span className="text-sm text-neutral-500">
                              {item.publication_year}
                            </span>
                          ) : null}
                        </div>

                        {item.evaluation_error ? (
                          <p className="mt-3 max-w-3xl text-sm leading-6 text-red-300">
                            {item.evaluation_error}
                          </p>
                        ) : null}
                      </div>

                      <Link
                        href={`/documents/${item.document_id}/curation`}
                        className={SECONDARY_BUTTON_CLASS_NAME}
                      >
                        Review evaluation
                      </Link>
                    </article>
                  ),
                )}

                {!dashboard.review_queue.length ? (
                  <div className="p-10 text-center text-neutral-500">
                    No evaluations require attention.
                  </div>
                ) : null}
              </div>
            </section>

            <section className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900">
              <div className="border-b border-neutral-800 p-6">
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                  Relationship review
                </p>

                <h2 className="mt-2 text-xl font-semibold text-white">
                  Duplicates and editions
                </h2>

                <p className="mt-2 text-sm text-neutral-400">
                  Confirm or reject potential
                  duplicate, overlapping, or
                  superseded books.
                </p>
              </div>

              <div className="divide-y divide-neutral-800">
                {dashboard.pending_relationships.map(
                  (relationship) => {
                    const actionInProgress =
                      relationshipActionId ===
                      relationship.relationship_id;

                    return (
                      <article
                        key={
                          relationship.relationship_id
                        }
                        className="space-y-5 p-6 transition hover:bg-neutral-800/30"
                      >
                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                          <div className="min-w-0">
                            <p className="font-medium text-white">
                              {relationshipDocumentLabel(
                                relationship
                                  .document_a_snapshot,
                                relationship
                                  .document_a_id,
                              )}
                            </p>

                            <p className="my-1 text-sm text-neutral-600">
                              compared with
                            </p>

                            <p className="font-medium text-white">
                              {relationshipDocumentLabel(
                                relationship
                                  .document_b_snapshot,
                                relationship
                                  .document_b_id,
                              )}
                            </p>
                          </div>

                          <div className="shrink-0 text-left md:text-right">
                            <StatusBadge
                              value={
                                relationship
                                  .relationship_type
                              }
                            />

                            <p className="mt-2 text-sm text-neutral-500">
                              Confidence:{" "}
                              <span className="font-medium text-neutral-300">
                                {(
                                  relationship.confidence *
                                  100
                                ).toFixed(1)}
                                %
                              </span>
                            </p>
                          </div>
                        </div>

                        {relationship.reasons?.length ? (
                          <ul className="list-disc space-y-1.5 pl-5 text-sm leading-6 text-neutral-400">
                            {relationship.reasons.map(
                              (reason) => (
                                <li key={reason}>
                                  {reason}
                                </li>
                              ),
                            )}
                          </ul>
                        ) : null}

                        {relationship.recommended_action ? (
                          <p className="text-sm text-neutral-500">
                            Recommended action:{" "}
                            <span className="font-medium text-neutral-300">
                              {formatLabel(
                                relationship
                                  .recommended_action,
                              )}
                            </span>
                          </p>
                        ) : null}

                        <div className="flex flex-wrap gap-3">
                          <button
                            type="button"
                            disabled={actionInProgress}
                            onClick={() =>
                              void handleRelationshipAction(
                                relationship,
                                "approve",
                              )
                            }
                            className="rounded-xl bg-white px-4 py-2 text-sm font-medium text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {actionInProgress
                              ? "Working…"
                              : "Approve"}
                          </button>

                          <button
                            type="button"
                            disabled={actionInProgress}
                            onClick={() =>
                              void handleRelationshipAction(
                                relationship,
                                "reject",
                              )
                            }
                            className={SECONDARY_BUTTON_CLASS_NAME}
                          >
                            Reject
                          </button>
                        </div>
                      </article>
                    );
                  },
                )}

                {!dashboard.pending_relationships.length ? (
                  <div className="p-10 text-center text-neutral-500">
                    No relationship candidates
                    require review.
                  </div>
                ) : null}
              </div>
            </section>
          </>
        ) : null}
      </section>
    </main>
  );
}