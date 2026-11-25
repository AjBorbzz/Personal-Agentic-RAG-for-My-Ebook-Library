"use client";

import { useState } from "react";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { StatusMessage } from "@/components/WorkspaceUI";
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
    setResult(null);

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
    <PageFrame width="narrow">
      <PageHeader
        title="Backend health"
        description="Check the connection between this workspace and the local FastAPI service."
      />
      <section
        className="workspace-panel space-y-4"
        aria-label="Connection check"
      >
        <button
          type="button"
          onClick={checkHealth}
          disabled={loading}
          className="workspace-button"
        >
          {loading ? "Checking…" : "Check connection"}
        </button>
        {loading && (
          <StatusMessage tone="info">Connecting to FastAPI…</StatusMessage>
        )}
        {result && (
          <StatusMessage tone="success">
            The backend responded with status {result.status}.
          </StatusMessage>
        )}
        {error && <StatusMessage tone="error">{error}</StatusMessage>}
      </section>
    </PageFrame>
  );
}
