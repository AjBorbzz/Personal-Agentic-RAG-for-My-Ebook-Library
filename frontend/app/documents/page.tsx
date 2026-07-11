"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPatch } from "@/lib/api";

type DocumentRecord = {
  document_id: string;

  filename: string | null;
  title: string | null;
  author: string | null;
  file_type: string | null;

  source_type: string | null;
  tool_name: string | null;
  tool_version: string | null;
  version_major: number | null;
  version_minor: number | null;

  publication_year: number | null;
  publication_date: string | null;

  primary_domain: string | null;
  domains: string[] | null;

  page_count: number | null;
  chunk_count: number | null;
  text_characters: number | null;

  content_hash: string | null;

  is_active: boolean;
  is_deprecated: boolean;
  superseded_by_document_id: string | null;

  saved_path: string | null;
  parsed_output_path: string | null;
  chunks_output_path: string | null;

  notes: string | null;

  ingested_at: string;
  created_at: string;
  updated_at: string;
};

type DeprecateRequest = {
  superseded_by_document_id: string | null;
  notes: string | null;
};

function buildDocumentsPath(filters: {
  toolName: string;
  isActive: string;
  isDeprecated: string;
  limit: number;
}) {
  const params = new URLSearchParams();

  if (filters.toolName.trim()) {
    params.set("tool_name", filters.toolName.trim());
  }

  if (filters.isActive !== "all") {
    params.set("is_active", filters.isActive);
  }

  if (filters.isDeprecated !== "all") {
    params.set("is_deprecated", filters.isDeprecated);
  }

  params.set("limit", String(filters.limit));

  return `/documents?${params.toString()}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "N/A";
  }

  return new Date(value).toLocaleString();
}

function StatusBadge({ document }: { document: DocumentRecord }) {
  if (document.is_deprecated) {
    return (
      <span className="rounded-full border border-yellow-700 bg-yellow-950 px-2 py-1 text-xs text-yellow-300">
        Deprecated
      </span>
    );
  }

  if (document.is_active) {
    return (
      <span className="rounded-full border border-green-700 bg-green-950 px-2 py-1 text-xs text-green-300">
        Active
      </span>
    );
  }

  return (
    <span className="rounded-full border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-300">
      Inactive
    </span>
  );
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [toolName, setToolName] = useState("");
  const [isActive, setIsActive] = useState("all");
  const [isDeprecated, setIsDeprecated] = useState("all");
  const [limit, setLimit] = useState(50);

  const [loading, setLoading] = useState(false);
  const [deprecatingId, setDeprecatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments() {
    setLoading(true);
    setError(null);

    try {
      const path = buildDocumentsPath({
        toolName,
        isActive,
        isDeprecated,
        limit,
      });

      const data = await apiGet<DocumentRecord[]>(path);
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function deprecateDocument(documentId: string) {
    const confirmed = window.confirm(
      "Mark this document as deprecated and inactive?"
    );

    if (!confirmed) {
      return;
    }

    setDeprecatingId(documentId);
    setError(null);

    const payload: DeprecateRequest = {
      superseded_by_document_id: null,
      notes: "Deprecated from Document Library UI.",
    };

    try {
      await apiPatch<DocumentRecord, DeprecateRequest>(
        `/documents/${documentId}/deprecate`,
        payload
      );

      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown deprecate error");
    } finally {
      setDeprecatingId(null);
    }
  }

  useEffect(() => {
    loadDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-7xl">
        <div className="mb-8">
          <Link href="/" className="text-sm text-neutral-400 hover:text-white">
            ← Back to dashboard
          </Link>

          <h1 className="mt-4 text-3xl font-bold">Document Library</h1>

          <p className="mt-3 max-w-3xl text-neutral-400">
            View registered documents from PostgreSQL, inspect version metadata,
            and mark old documents as deprecated so retrieval avoids outdated
            content by default.
          </p>
        </div>

        <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <div className="grid gap-4 md:grid-cols-5">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-neutral-300">
                Tool Name
              </label>
              <input
                value={toolName}
                onChange={(event) => setToolName(event.target.value)}
                placeholder="django, fastapi, azure"
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Active
              </label>
              <select
                value={isActive}
                onChange={(event) => setIsActive(event.target.value)}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              >
                <option value="all">All</option>
                <option value="true">Active only</option>
                <option value="false">Inactive only</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Deprecated
              </label>
              <select
                value={isDeprecated}
                onChange={(event) => setIsDeprecated(event.target.value)}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              >
                <option value="all">All</option>
                <option value="true">Deprecated only</option>
                <option value="false">Non-deprecated only</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Limit
              </label>
              <input
                type="number"
                min={1}
                max={200}
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>
          </div>

          <button
            onClick={loadDocuments}
            disabled={loading}
            className="mt-5 rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
          >
            {loading ? "Loading..." : "Load Documents"}
          </button>
        </section>

        {error && (
          <pre className="mt-6 overflow-auto rounded-xl border border-red-900 bg-red-950 p-4 text-sm text-red-200">
            {error}
          </pre>
        )}

        <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <div className="mb-5 flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold">Registered Documents</h2>
            <p className="text-sm text-neutral-500">
              {documents.length} document(s)
            </p>
          </div>

          <div className="space-y-4">
            {documents.map((document) => (
              <div
                key={document.document_id}
                className="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-white">
                        {document.title || document.filename || "Untitled"}
                      </h3>

                      <StatusBadge document={document} />
                    </div>

                    <p className="mt-1 text-sm text-neutral-500">
                      {document.filename || "Unknown file"}
                    </p>
                  </div>

                  <button
                    onClick={() => deprecateDocument(document.document_id)}
                    disabled={
                      document.is_deprecated ||
                      deprecatingId === document.document_id
                    }
                    className="rounded-lg border border-yellow-800 px-3 py-1.5 text-xs text-yellow-300 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {deprecatingId === document.document_id
                      ? "Deprecating..."
                      : "Mark Deprecated"}
                  </button>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-3 lg:grid-cols-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Document ID
                    </p>
                    <p className="mt-1 break-all font-mono text-xs text-neutral-300">
                      {document.document_id}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Tool
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.tool_name || "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Version
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.tool_version ||
                        document.version_major ||
                        "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Source Type
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.source_type || "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Publication Year
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.publication_year ?? "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Chunks
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.chunk_count ?? "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Pages
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.page_count ?? "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Ingested
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {formatDate(document.ingested_at)}
                    </p>
                  </div>
                </div>

                <div className="mt-4 rounded-lg border border-neutral-800 bg-neutral-900 p-3">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Domains
                  </p>
                  <p className="mt-1 text-sm text-neutral-300">
                    {(document.domains || []).join(", ") || "N/A"}
                  </p>
                </div>

                {document.notes && (
                  <div className="mt-3 rounded-lg border border-neutral-800 bg-neutral-900 p-3">
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Notes
                    </p>
                    <p className="mt-1 text-sm text-neutral-300">
                      {document.notes}
                    </p>
                  </div>
                )}
              </div>
            ))}

            {!loading && documents.length === 0 && (
              <p className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 text-sm text-neutral-400">
                No documents found.
              </p>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}