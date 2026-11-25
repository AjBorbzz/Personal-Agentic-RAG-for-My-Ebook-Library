"use client";

import Link from "next/link";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { type ReactNode, useEffect, useState } from "react";

import { fetchBookSkillDashboard } from "@/lib/book-skill-dashboard-api";

import type { BookSkillDashboard } from "@/lib/book-skill-dashboard-types";

const PANEL_CLASS_NAME = "workspace-panel";

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

function StatCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: ReactNode;
  helper?: string;
}) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
        {label}
      </p>

      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>

      {helper ? (
        <p className="mt-2 text-sm text-neutral-500">{helper}</p>
      ) : null}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <span className="inline-flex rounded-full border border-neutral-700 bg-neutral-950 px-2.5 py-1 text-xs font-medium text-neutral-300">
      {score.toFixed(1)}
    </span>
  );
}

export default function BookSkillDashboardPage() {
  const [dashboard, setDashboard] = useState<BookSkillDashboard | null>(null);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [requestCount, setRequestCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetchBookSkillDashboard(selectedDomain || undefined, 15, {
      signal: controller.signal,
    })
      .then((result) => {
        if (!controller.signal.aborted) setDashboard(result);
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load the dashboard.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [selectedDomain, requestCount]);

  function refresh() {
    setLoading(true);
    setError(null);
    setRequestCount((count) => count + 1);
  }

  return (
    <PageFrame width="wide" className="space-y-6">
      <PageHeader
        title="Book-to-Skill Dashboard"
        description="See which technical skills your ebook library covers, which books support them, and where coverage is missing."
      />

      {error && <StatusMessage tone="error">{error}</StatusMessage>}

      <section className={PANEL_CLASS_NAME}>
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
              Dashboard scope
            </p>

            <h2 className="mt-2 text-xl font-semibold text-white">
              Filter by skill domain
            </h2>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <Field label="Skill domain">
              <select
                value={selectedDomain}
                onChange={(event) => {
                  setLoading(true);
                  setError(null);
                  setSelectedDomain(event.target.value);
                }}
                className="workspace-field"
              >
                <option value="">All domains</option>
                {dashboard?.domains.map((domain) => (
                  <option key={domain.slug} value={domain.slug}>
                    {domain.name}
                  </option>
                ))}
              </select>
            </Field>

            <button
              type="button"
              disabled={loading}
              onClick={refresh}
              className="workspace-button workspace-button--secondary"
            >
              {loading ? "Loading…" : "Refresh"}
            </button>

            <Link
              href="/skill-taxonomy"
              className="workspace-button workspace-button--secondary"
            >
              Skill taxonomy
            </Link>
          </div>
        </div>
      </section>

      {loading && (
        <StatusMessage tone="info">
          Loading book-to-skill dashboard…
        </StatusMessage>
      )}

      {dashboard ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Registered books"
              value={dashboard.stats.registered_documents}
            />

            <StatCard
              label="Mapped books"
              value={dashboard.stats.books_with_any_mappings}
              helper="Books with at least one candidate"
            />

            <StatCard
              label="Approved books"
              value={dashboard.stats.books_with_approved_mappings}
              helper="Books with trusted mappings"
            />

            <StatCard
              label="Pending reviews"
              value={dashboard.stats.pending_mappings}
            />

            <StatCard
              label="Approved mappings"
              value={dashboard.stats.approved_mappings}
            />

            <StatCard
              label="Primary mappings"
              value={dashboard.stats.primary_mappings}
            />

            <StatCard
              label="Covered skills"
              value={dashboard.stats.skills_with_approved_books}
              helper={`of ${dashboard.stats.active_skills} active skills`}
            />

            <StatCard
              label="Unmapped skills"
              value={dashboard.stats.unmapped_active_skills}
              helper="No approved supporting book"
            />
          </div>

          <section className={PANEL_CLASS_NAME}>
            <h2 className="text-xl font-semibold text-white">Mapping status</h2>

            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {dashboard.status_counts.map((item) => (
                <div
                  key={item.status}
                  className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4"
                >
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    {formatLabel(item.status)}
                  </p>

                  <p className="mt-2 text-2xl font-semibold text-white">
                    {item.count}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className={PANEL_CLASS_NAME}>
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                Library ranking
              </p>

              <h2 className="mt-2 text-xl font-semibold text-white">
                Strongest books by skill coverage
              </h2>
            </div>

            {dashboard.top_books.length ? (
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-800 text-left text-sm">
                  <thead>
                    <tr className="text-neutral-500">
                      <th className="px-3 py-3 font-medium">Book</th>

                      <th className="px-3 py-3 font-medium">Quality</th>

                      <th className="px-3 py-3 font-medium">Mappings</th>

                      <th className="px-3 py-3 font-medium">Primary skills</th>

                      <th className="px-3 py-3 font-medium">Action</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-neutral-800">
                    {dashboard.top_books.map((book) => (
                      <tr key={book.document_id}>
                        <td className="px-3 py-4">
                          <p className="font-medium text-white">
                            {book.document_title}
                          </p>

                          {book.author ? (
                            <p className="mt-1 text-xs text-neutral-500">
                              {book.author}
                            </p>
                          ) : null}
                        </td>

                        <td className="px-3 py-4">
                          <ScoreBadge score={book.average_quality_score} />
                        </td>

                        <td className="px-3 py-4 text-neutral-300">
                          {book.approved_mapping_count}
                        </td>

                        <td className="px-3 py-4">
                          <div className="flex max-w-md flex-wrap gap-2">
                            {book.primary_skills.map((skill) => (
                              <span
                                key={skill}
                                className="rounded-full border border-blue-900/70 bg-blue-950/40 px-2 py-1 text-xs text-blue-300"
                              >
                                {skill}
                              </span>
                            ))}

                            {!book.primary_skills.length ? (
                              <span className="text-neutral-600">—</span>
                            ) : null}
                          </div>
                        </td>

                        <td className="px-3 py-4">
                          <Link
                            href={`/documents/${book.document_id}/skills`}
                            className="text-blue-400 hover:text-blue-300 hover:underline"
                          >
                            View mappings
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-6 text-sm text-neutral-500">
                No approved mappings are available yet.
              </p>
            )}
          </section>

          <section className={PANEL_CLASS_NAME}>
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
                Skill coverage
              </p>

              <h2 className="mt-2 text-xl font-semibold text-white">
                Best-supported skills
              </h2>
            </div>

            {dashboard.top_skills.length ? (
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-800 text-left text-sm">
                  <thead>
                    <tr className="text-neutral-500">
                      <th className="px-3 py-3 font-medium">Skill</th>

                      <th className="px-3 py-3 font-medium">Books</th>

                      <th className="px-3 py-3 font-medium">Quality</th>

                      <th className="px-3 py-3 font-medium">Best book</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-neutral-800">
                    {dashboard.top_skills.map((skill) => (
                      <tr key={skill.skill_id}>
                        <td className="px-3 py-4">
                          <p className="font-medium text-white">
                            {skill.skill_name}
                          </p>

                          <p className="mt-1 text-xs text-neutral-500">
                            {skill.domain_name}
                            {skill.category_name
                              ? ` · ${skill.category_name}`
                              : ""}
                          </p>
                        </td>

                        <td className="px-3 py-4 text-neutral-300">
                          {skill.supporting_book_count}
                        </td>

                        <td className="px-3 py-4">
                          <ScoreBadge score={skill.average_quality_score} />
                        </td>

                        <td className="px-3 py-4">
                          {skill.best_document_id ? (
                            <Link
                              href={`/documents/${skill.best_document_id}/skills`}
                              className="text-blue-400 hover:text-blue-300 hover:underline"
                            >
                              {skill.best_document_title}
                            </Link>
                          ) : (
                            <span className="text-neutral-600">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-6 text-sm text-neutral-500">
                No approved skill coverage is available yet.
              </p>
            )}
          </section>

          <div className="grid gap-6 xl:grid-cols-2">
            <section className={PANEL_CLASS_NAME}>
              <h2 className="text-xl font-semibold text-white">
                Pending reviews
              </h2>

              {dashboard.pending_reviews.length ? (
                <div className="mt-5 space-y-3">
                  {dashboard.pending_reviews.map((review) => (
                    <div
                      key={review.mapping_id}
                      className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4"
                    >
                      <p className="font-medium text-white">
                        {review.skill_name}
                      </p>

                      <p className="mt-1 text-sm text-neutral-400">
                        {review.document_title}
                      </p>

                      <p className="mt-2 text-xs text-neutral-600">
                        Version {review.mapping_version}
                        {" · "}
                        {formatDate(review.candidate_generated_at)}
                      </p>

                      <Link
                        href={`/documents/${review.document_id}/skills`}
                        className="mt-3 inline-block text-sm text-blue-400 hover:text-blue-300 hover:underline"
                      >
                        Review mapping
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-5 text-sm text-neutral-500">
                  No mappings are awaiting review.
                </p>
              )}
            </section>

            <section className={PANEL_CLASS_NAME}>
              <h2 className="text-xl font-semibold text-white">
                Skills without books
              </h2>

              <p className="mt-2 text-sm leading-6 text-neutral-500">
                These active taxonomy skills have no approved supporting book.
              </p>

              {dashboard.unmapped_skills.length ? (
                <div className="mt-5 space-y-3">
                  {dashboard.unmapped_skills.map((skill) => (
                    <div
                      key={skill.skill_id}
                      className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4"
                    >
                      <p className="font-medium text-white">
                        {skill.skill_name}
                      </p>

                      <p className="mt-1 text-xs text-neutral-500">
                        {skill.domain_name}
                        {skill.category_name ? ` · ${skill.category_name}` : ""}
                      </p>

                      <div className="mt-3 flex flex-wrap gap-2">
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
                          {formatLabel(skill.skill_type)}
                        </span>

                        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
                          {formatLabel(skill.difficulty_level)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-5 text-sm text-emerald-300">
                  Every active skill has an approved supporting book.
                </p>
              )}
            </section>
          </div>
        </>
      ) : null}
    </PageFrame>
  );
}
