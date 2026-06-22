"use client";

import { useState } from "react";
import { apiGet } from "@/lib/api";

type HealthResponse = {
  status: string;
};

export default function HealthPage() {
  const [result, setResult] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function checkHealth() {
    setLoading(true);
    setError(null);

    try {
      const data = await apiGet<HealthResponse>("/health");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-bold">Backend Health Check</h1>
        <p className="mt-3 text-neutral-400">
          Use this to confirm the Next.js frontend can reach your FastAPI backend.
        </p>

        <button
          onClick={checkHealth}
          disabled={loading}
          className="mt-6 rounded-lg bg-white px-4 py-2 font-medium text-black disabled:opacity-50"
        >
          {loading ? "Checking..." : "Check Backend"}
        </button>

        {result && (
          <pre className="mt-6 overflow-auto rounded-lg border border-neutral-800 bg-neutral-900 p-4 text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}

        {error && (
          <pre className="mt-6 overflow-auto rounded-lg border border-red-900 bg-red-950 p-4 text-sm text-red-200">
            {error}
          </pre>
        )}
      </section>
    </main>
  );
}