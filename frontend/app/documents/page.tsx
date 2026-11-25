"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { apiGet, apiPatch } from "@/lib/api";

type DocumentRecord = {
  document_id: string;
  filename: string | null;
  title: string | null;
  source_type: string | null;
  tool_name: string | null;
  tool_version: string | null;
  version_major: number | null;
  publication_year: number | null;
  domains: string[] | null;
  page_count: number | null;
  chunk_count: number | null;
  is_active: boolean;
  is_deprecated: boolean;
  notes: string | null;
  ingested_at: string;
  metadata_review_status: string;
};

type DeprecateRequest = {
  superseded_by_document_id: string | null;
  notes: string | null;
};

const DEFAULT_FILTERS = {
  toolName: "",
  isActive: "all",
  isDeprecated: "all",
  limit: 50,
};

function buildDocumentsPath(filters: typeof DEFAULT_FILTERS) {
  const params = new URLSearchParams({ limit: String(filters.limit) });
  const toolName = filters.toolName.trim();

  if (toolName) params.set("tool_name", toolName);
  if (filters.isActive !== "all") params.set("is_active", filters.isActive);
  if (filters.isDeprecated !== "all")
    params.set("is_deprecated", filters.isDeprecated);

  return `/documents?${params.toString()}`;
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function DocumentCard({
  document,
  deprecatingId,
  onDeprecate,
}: {
  document: DocumentRecord;
  deprecatingId: string | null;
  onDeprecate: (documentId: string) => void;
}) {
  const documentPath = `/documents/${encodeURIComponent(document.document_id)}`;
  const status = document.is_deprecated
    ? "Deprecated"
    : document.is_active
      ? "Active"
      : "Inactive";
  const statusClass = {
    Deprecated: "border-yellow-700 bg-yellow-950 text-yellow-300",
    Active: "border-green-700 bg-green-950 text-green-300",
    Inactive: "",
  }[status];
  const details = [
    { label: "Document ID", value: document.document_id, mono: true },
    { label: "Tool", value: document.tool_name },
    {
      label: "Version",
      value: document.tool_version || document.version_major,
    },
    { label: "Source type", value: document.source_type },
    { label: "Publication year", value: document.publication_year },
    { label: "Chunks", value: document.chunk_count },
    { label: "Pages", value: document.page_count },
    { label: "Ingested", value: formatDate(document.ingested_at) },
  ];

  return (
    <article className="min-w-0 rounded-xl border border-neutral-800 bg-neutral-950 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 max-w-full flex-[1_1_20rem]">
          <h3 className="font-semibold text-white [overflow-wrap:anywhere]">
            {document.title || document.filename || "Untitled"}
          </h3>
          <p className="mt-1 text-sm text-neutral-400 [overflow-wrap:anywhere]">
            {document.filename || "Unknown file"}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className={`workspace-badge ${statusClass}`}>{status}</span>
            <span className="workspace-badge">
              Metadata {document.metadata_review_status.replaceAll("_", " ")}
            </span>
          </div>
        </div>

        <div className="flex min-w-0 flex-wrap gap-2">
          <Link
            className="workspace-button workspace-button--secondary"
            href={`${documentPath}/metadata`}
          >
            Review metadata
          </Link>
          <Link
            className="workspace-button workspace-button--secondary"
            href={`${documentPath}/skills`}
          >
            Review skills
          </Link>
          <button
            type="button"
            className="workspace-button workspace-button--secondary"
            disabled={document.is_deprecated || deprecatingId !== null}
            onClick={() => onDeprecate(document.document_id)}
          >
            {deprecatingId === document.document_id
              ? "Deprecating…"
              : "Mark deprecated"}
          </button>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
        {details.map(({ label, value, mono }) => (
          <div key={label} className="min-w-0">
            <dt className="text-xs uppercase tracking-wide text-neutral-400">
              {label}
            </dt>
            <dd
              className={`mt-1 text-sm text-neutral-300 [overflow-wrap:anywhere] ${
                mono ? "font-mono text-xs" : ""
              }`}
            >
              {value ?? "N/A"}
            </dd>
          </div>
        ))}
      </dl>

      <dl className="mt-4 min-w-0 space-y-3">
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-3">
          <dt className="text-xs uppercase tracking-wide text-neutral-400">
            Domains
          </dt>
          <dd className="mt-1 text-sm text-neutral-300 [overflow-wrap:anywhere]">
            {document.domains?.join(", ") || "N/A"}
          </dd>
        </div>
        {document.notes && (
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-3">
            <dt className="text-xs uppercase tracking-wide text-neutral-400">
              Notes
            </dt>
            <dd className="mt-1 text-sm text-neutral-300 [overflow-wrap:anywhere]">
              {document.notes}
            </dd>
          </div>
        )}
      </dl>
    </article>
  );
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(true);
  const [deprecatingId, setDeprecatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    apiGet<DocumentRecord[]>(buildDocumentsPath(appliedFilters), {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) setDocuments(data);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Could not load documents.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [appliedFilters]);

  function refresh(nextFilters: typeof DEFAULT_FILTERS) {
    setLoading(true);
    setError(null);
    setAppliedFilters({ ...nextFilters });
  }

  async function deprecateDocument(documentId: string) {
    if (!window.confirm("Mark this document as deprecated and inactive?"))
      return;

    setDeprecatingId(documentId);
    setError(null);
    setNotice(null);

    try {
      await apiPatch<DocumentRecord, DeprecateRequest>(
        `/documents/${encodeURIComponent(documentId)}/deprecate`,
        {
          superseded_by_document_id: null,
          notes: "Deprecated from Document Library UI.",
        },
      );

      setNotice("Document marked as deprecated.");
      refresh(appliedFilters);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not deprecate the document.",
      );
    } finally {
      setDeprecatingId(null);
    }
  }

  return (
    <PageFrame width="wide" className="space-y-6">
      <PageHeader
        title="Document Library"
        description="Inspect ebook editions, review their metadata and skill mappings, and retire outdated sources from retrieval."
      />

      <form
        className="workspace-panel"
        onSubmit={(event) => {
          event.preventDefault();
          setNotice(null);
          refresh(filters);
        }}
      >
        <div className="grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Tool name">
            <input
              value={filters.toolName}
              onChange={(event) =>
                setFilters({ ...filters, toolName: event.target.value })
              }
              placeholder="Django, FastAPI, Azure"
              className="workspace-field"
            />
          </Field>
          <Field label="Active">
            <select
              value={filters.isActive}
              onChange={(event) =>
                setFilters({ ...filters, isActive: event.target.value })
              }
              className="workspace-field"
            >
              <option value="all">All</option>
              <option value="true">Active only</option>
              <option value="false">Inactive only</option>
            </select>
          </Field>
          <Field label="Deprecated">
            <select
              value={filters.isDeprecated}
              onChange={(event) =>
                setFilters({ ...filters, isDeprecated: event.target.value })
              }
              className="workspace-field"
            >
              <option value="all">All</option>
              <option value="true">Deprecated only</option>
              <option value="false">Non-deprecated only</option>
            </select>
          </Field>
          <Field label="Limit">
            <input
              type="number"
              min={1}
              max={200}
              required
              value={filters.limit || ""}
              onChange={(event) =>
                setFilters({ ...filters, limit: Number(event.target.value) })
              }
              className="workspace-field"
            />
          </Field>
        </div>

        <button
          type="submit"
          disabled={loading || deprecatingId !== null}
          className="workspace-button mt-5"
        >
          {loading ? "Loading…" : "Load documents"}
        </button>
      </form>

      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {notice && <StatusMessage tone="success">{notice}</StatusMessage>}
      {loading && <StatusMessage tone="info">Loading documents…</StatusMessage>}

      <section className="workspace-panel min-w-0" aria-busy={loading}>
        <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-xl font-semibold">Registered documents</h2>
          <p className="text-sm text-neutral-400">
            {documents.length}{" "}
            {documents.length === 1 ? "document" : "documents"}
          </p>
        </div>

        <div className="min-w-0 space-y-4">
          {documents.map((document) => (
            <DocumentCard
              key={document.document_id}
              document={document}
              deprecatingId={deprecatingId}
              onDeprecate={deprecateDocument}
            />
          ))}

          {!loading && !error && documents.length === 0 && (
            <StatusMessage tone="info">
              No documents match the selected filters.
            </StatusMessage>
          )}
        </div>
      </section>
    </PageFrame>
  );
}
