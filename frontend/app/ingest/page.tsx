"use client";

import { useState } from "react";
import Link from "next/link";
import { apiPost, apiUpload } from "@/lib/api";

type IngestResponse = {
  document_id: string;
  filename: string;
  saved_path: string;
  file_type: string;
  title: string | null;
  author: string | null;
  page_count: number | null;
  primary_domain: string;
  domains: string[];
  text_characters: number;
  chunk_count: number;
  parsed_output_path: string;
  chunks_output_path: string;
  elapsed_seconds: number;
  elapsed_ms: number;
};

type IndexResponse = {
  document_id: string;
  collection_name: string;
  filename: string | null;
  title: string | null;
  primary_domain: string;
  domains: string[];
  chunk_count: number;
  indexed_count: number;
  embedding_dimension: number;
  elapsed_seconds: number;
  elapsed_ms: number;
};

type EmptyBody = Record<string, never>;

export default function IngestPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);
  const [indexResult, setIndexResult] = useState<IndexResponse | null>(null);

  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function uploadFile() {
    if (!selectedFile) {
      setError("Please select a file first.");
      return;
    }

    setUploading(true);
    setError(null);
    setIngestResult(null);
    setIndexResult(null);

    try {
      const data = await apiUpload<IngestResponse>("/ingest", selectedFile);
      setIngestResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown upload error");
    } finally {
      setUploading(false);
    }
  }

  async function indexDocument() {
    if (!ingestResult?.document_id) {
      setError("No document_id available. Ingest a file first.");
      return;
    }

    setIndexing(true);
    setError(null);
    setIndexResult(null);

    try {
      const data = await apiPost<IndexResponse, EmptyBody>(
        `/index/${ingestResult.document_id}`,
        {}
      );

      setIndexResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown indexing error");
    } finally {
      setIndexing(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-5xl">
        <div className="mb-8">
          <Link href="/" className="text-sm text-neutral-400 hover:text-white">
            ← Back to dashboard
          </Link>

          <h1 className="mt-4 text-3xl font-bold">Ingest and Index</h1>
          <p className="mt-3 max-w-3xl text-neutral-400">
            Upload a PDF, EPUB, or TXT file, extract and chunk the text, then
            index the chunks into Qdrant for semantic search and RAG.
          </p>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <label className="block text-sm font-medium text-neutral-300">
            Select ebook or document
          </label>

          <input
            type="file"
            accept=".pdf,.epub,.txt"
            onChange={(event) => {
              const file = event.target.files?.[0] || null;
              setSelectedFile(file);
              setIngestResult(null);
              setIndexResult(null);
              setError(null);
            }}
            className="mt-3 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 file:mr-4 file:rounded-lg file:border-0 file:bg-white file:px-4 file:py-2 file:text-sm file:font-medium file:text-black"
          />

          {selectedFile && (
            <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-4 text-sm text-neutral-300">
              <p>
                <span className="text-neutral-500">File:</span>{" "}
                {selectedFile.name}
              </p>
              <p>
                <span className="text-neutral-500">Size:</span>{" "}
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <p>
                <span className="text-neutral-500">Type:</span>{" "}
                {selectedFile.type || "Unknown"}
              </p>
            </div>
          )}

          <button
            onClick={uploadFile}
            disabled={uploading || !selectedFile}
            className="mt-5 rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
          >
            {uploading ? "Ingesting..." : "Ingest File"}
          </button>
        </div>

        {error && (
          <pre className="mt-6 overflow-auto rounded-xl border border-red-900 bg-red-950 p-4 text-sm text-red-200">
            {error}
          </pre>
        )}

        {ingestResult && (
          <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <div className="mb-3 flex flex-wrap gap-2 text-xs text-neutral-400">
              <span>Elapsed: {ingestResult.elapsed_seconds}s</span>
              <span>•</span>
              <span>Chunks: {ingestResult.chunk_count}</span>
              <span>•</span>
              <span>Characters: {ingestResult.text_characters}</span>
            </div>

            <h2 className="text-xl font-semibold">Ingestion Result</h2>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Document ID
                </p>
                <p className="mt-2 break-all font-mono text-sm">
                  {ingestResult.document_id}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Filename
                </p>
                <p className="mt-2 text-sm">{ingestResult.filename}</p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Title
                </p>
                <p className="mt-2 text-sm">
                  {ingestResult.title || "Unknown"}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Author
                </p>
                <p className="mt-2 text-sm">
                  {ingestResult.author || "Unknown"}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  File Type
                </p>
                <p className="mt-2 text-sm">{ingestResult.file_type}</p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Page Count
                </p>
                <p className="mt-2 text-sm">
                  {ingestResult.page_count ?? "N/A"}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Primary Domain
                </p>
                <p className="mt-2 text-sm">{ingestResult.primary_domain}</p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Domains
                </p>
                <p className="mt-2 text-sm">
                  {ingestResult.domains.join(", ") || "N/A"}
                </p>
              </div>
            </div>

            <div className="mt-5">
              <button
                onClick={indexDocument}
                disabled={indexing}
                className="rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
              >
                {indexing ? "Indexing..." : "Index Document"}
              </button>
            </div>
          </section>
        )}

        {indexResult && (
          <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <div className="mb-3 flex flex-wrap gap-2 text-xs text-neutral-400">
              <span>Elapsed: {indexResult.elapsed_seconds}s</span>
              <span>•</span>
              <span>Collection: {indexResult.collection_name}</span>
              <span>•</span>
              <span>Embedding dim: {indexResult.embedding_dimension}</span>
            </div>

            <h2 className="text-xl font-semibold">Indexing Result</h2>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Document ID
                </p>
                <p className="mt-2 break-all font-mono text-sm">
                  {indexResult.document_id}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Indexed Count
                </p>
                <p className="mt-2 text-sm">{indexResult.indexed_count}</p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Chunk Count
                </p>
                <p className="mt-2 text-sm">{indexResult.chunk_count}</p>
              </div>

              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-xs uppercase tracking-wide text-neutral-500">
                  Domains
                </p>
                <p className="mt-2 text-sm">
                  {indexResult.domains.join(", ") || "N/A"}
                </p>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="/search"
                className="rounded-xl border border-neutral-700 px-5 py-2 text-sm font-medium text-neutral-200 hover:border-neutral-500"
              >
                Go to Search
              </Link>

              <Link
                href="/rag-chat"
                className="rounded-xl border border-neutral-700 px-5 py-2 text-sm font-medium text-neutral-200 hover:border-neutral-500"
              >
                Ask in RAG Chat
              </Link>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}