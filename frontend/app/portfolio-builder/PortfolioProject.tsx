"use client";

import { useEffect, useState } from "react";
import { SectionNav, StatusMessage } from "@/components/WorkspaceUI";
import {
  portfolioApi,
  type Artifact,
  type Milestone,
  type Project,
  type Readiness,
} from "@/lib/portfolio-api";
import type { ProjectView } from "./PortfolioWorkspace";
import {
  ArtifactsPanel,
  BlueprintsPanel,
  MilestonesPanel,
  PublicationPanel,
  portfolioProjectPath,
} from "./PortfolioProjectSections";

type ProjectDetails = {
  project: Project;
  milestones?: Milestone[];
  artifacts?: Artifact[];
  readiness?: Readiness;
  warnings: string[];
};

type ProjectResult = {
  revision: number;
  details?: ProjectDetails;
  error?: string;
};

const projectStatuses = [
  "planned",
  "in_progress",
  "blocked",
  "completed",
  "published",
  "archived",
] as const;

export function PortfolioProject({
  id,
  view,
}: {
  id: string;
  view: ProjectView;
}) {
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<ProjectResult | null>(null);
  const [mutating, setMutating] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    loadProject(id, view, controller.signal).then(
      (details) => {
        if (!controller.signal.aborted) setResult({ details, revision });
      },
      (cause) => {
        if (!controller.signal.aborted) {
          setResult((previous) => ({
            details: previous?.details,
            revision,
            error: requestError(cause),
          }));
        }
      },
    );
    return () => controller.abort();
  }, [id, view, revision]);

  const loading = result?.revision !== revision;
  const busy = mutating || loading;
  const details = result?.details;
  const project = details?.project;
  const path = portfolioProjectPath(id);
  const items = [
    { label: "Project overview", href: path },
    { label: "Architecture", href: `${path}/architecture` },
    { label: "Artifacts", href: `${path}/artifacts` },
  ];

  async function run(task: () => Promise<unknown>, success: string) {
    if (busy) return false;
    setMutating(true);
    setError("");
    setNotice("");
    try {
      await task();
      setNotice(success);
      setRevision((current) => current + 1);
      return true;
    } catch (cause) {
      setError(requestError(cause));
      return false;
    } finally {
      setMutating(false);
    }
  }

  return (
    <div className="space-y-4" aria-busy={busy}>
      <SectionNav label="Project sections" items={items} />
      {loading && (
        <StatusMessage tone="info">Loading project data…</StatusMessage>
      )}
      {(error || (!loading && result?.error)) && (
        <StatusMessage tone="error">{error || result?.error}</StatusMessage>
      )}
      {notice && <StatusMessage tone="success">{notice}</StatusMessage>}
      {!loading &&
        details?.warnings.map((warning) => (
          <StatusMessage key={warning} tone="error">
            {warning}
          </StatusMessage>
        ))}
      {project && (
        <>
          <section className="workspace-panel space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-xl font-semibold wrap-anywhere">
                {project.title}
              </h2>
              <span className="workspace-badge">
                {displayLabel(project.status)}
              </span>
            </div>
            <p className="wrap-anywhere">{project.problem_statement}</p>
            <dl className="grid gap-3 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-neutral-400">Approved blueprint</dt>
                <dd>
                  {project.approved_blueprint_version ?? "Pending review"}
                </dd>
              </div>
              <div>
                <dt className="text-neutral-400">Target skills</dt>
                <dd className="wrap-anywhere">
                  {project.target_skill_ids.join(", ") || "None"}
                </dd>
              </div>
              <div>
                <dt className="text-neutral-400">Approved mappings</dt>
                <dd>{project.source_mapping_ids.length}</dd>
              </div>
            </dl>
            <div className="flex flex-wrap gap-2">
              {projectStatuses.map((status) => (
                <button
                  key={status}
                  type="button"
                  className="workspace-button workspace-button--secondary"
                  disabled={busy || project.status === status}
                  onClick={() =>
                    void run(
                      () => portfolioApi.status(id, status),
                      `Project status updated to ${displayLabel(
                        status,
                      ).toLowerCase()}.`,
                    )
                  }
                >
                  {displayLabel(status)}
                </button>
              ))}
            </div>
          </section>
          {view !== "artifacts" && (
            <BlueprintsPanel
              project={project}
              showArchitecture={view === "architecture"}
              busy={busy}
              run={run}
            />
          )}
          {view === "project" && details.milestones && (
            <MilestonesPanel
              id={id}
              milestones={details.milestones}
              busy={busy}
              run={run}
            />
          )}
          {view !== "architecture" && details.artifacts && (
            <ArtifactsPanel
              id={id}
              artifacts={details.artifacts}
              busy={busy}
              run={run}
            />
          )}
          {view === "project" && details.readiness && (
            <PublicationPanel id={id} readiness={details.readiness} />
          )}
        </>
      )}
    </div>
  );
}

async function loadProject(
  id: string,
  view: ProjectView,
  signal: AbortSignal,
): Promise<ProjectDetails> {
  const options = { signal };
  const project = await portfolioApi.project(id, options);
  const [milestones, artifacts, readiness] = await Promise.allSettled([
    view === "project" ? portfolioApi.milestones(id, options) : undefined,
    view !== "architecture" ? portfolioApi.artifacts(id, options) : undefined,
    view === "project" ? portfolioApi.readiness(id, options) : undefined,
  ]);

  const warnings = [
    milestones.status === "rejected"
      ? `Milestones could not load: ${requestError(milestones.reason)}`
      : "",
    artifacts.status === "rejected"
      ? `Artifacts could not load: ${requestError(artifacts.reason)}`
      : "",
    readiness.status === "rejected"
      ? `Publication readiness could not load: ${requestError(
          readiness.reason,
        )}`
      : "",
  ].filter(Boolean);

  return {
    project,
    milestones:
      milestones.status === "fulfilled" ? milestones.value : undefined,
    artifacts: artifacts.status === "fulfilled" ? artifacts.value : undefined,
    readiness: readiness.status === "fulfilled" ? readiness.value : undefined,
    warnings,
  };
}

function displayLabel(status: string) {
  return status
    .replaceAll("_", " ")
    .replace(/^./, (first) => first.toUpperCase());
}

function requestError(cause: unknown) {
  return cause instanceof Error ? cause.message : String(cause);
}
