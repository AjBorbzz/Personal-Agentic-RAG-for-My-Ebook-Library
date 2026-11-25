"use client";

import Link from "next/link";
import { useState } from "react";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import {
  portfolioApi,
  type Artifact,
  type Milestone,
  type Project,
  type Readiness,
} from "@/lib/portfolio-api";

type RunAction = (
  task: () => Promise<unknown>,
  notice: string,
) => Promise<boolean>;
type PanelProps = { busy: boolean; run: RunAction };

const secondary = "workspace-button workspace-button--secondary";
const draftKinds = [
  "README",
  "architecture",
  "case_study",
  "resume_bullet",
  "interview_story",
];
const artifactTypes = [
  "repository",
  "architecture",
  "README",
  "test_report",
  "demo",
  "case_study",
  "resume_bullet",
  "interview_story",
  "publication",
];
const claimScopes = [
  "planned",
  "implemented",
  "tested",
  "measured",
  "published",
];
const verificationStatuses = ["draft", "reviewed", "verified", "published"];

export function portfolioProjectPath(id: string) {
  return `/portfolio-builder/projects/${encodeURIComponent(id)}`;
}

export function BlueprintsPanel({
  project,
  showArchitecture,
  busy,
  run,
}: PanelProps & {
  project: Project;
  showArchitecture: boolean;
}) {
  const [specification, setSpecification] = useState("");
  const [notes, setNotes] = useState(
    "Reviewed specification against the stated scope and source links.",
  );

  async function saveBlueprint(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!specification.trim()) return;
    const saved = await run(
      async () =>
        portfolioApi.blueprint(
          project.portfolio_project_id,
          jsonObject(specification),
        ),
      "Blueprint version saved for human review.",
    );
    if (saved) setSpecification("");
  }

  return (
    <section className="workspace-panel space-y-4">
      <h2 className="text-xl font-semibold">Blueprints</h2>
      <p className="text-sm text-neutral-400">
        Generate a specification in the{" "}
        <Link className="underline" href="/project-generator">
          Project Generator
        </Link>
        , review it against your project scope, then save the full JSON for
        approval.
      </p>
      <form className="space-y-3" onSubmit={saveBlueprint}>
        <Field label="Project Generator JSON">
          <textarea
            className="workspace-field font-mono"
            rows={7}
            value={specification}
            onChange={(event) => setSpecification(event.target.value)}
            required
          />
        </Field>
        <button
          className="workspace-button"
          disabled={busy || !specification.trim()}
        >
          Save blueprint version
        </button>
      </form>
      {project.blueprint_versions.length > 0 && (
        <div className="space-y-3">
          <Field label="Blueprint approval notes">
            <textarea
              className="workspace-field"
              rows={2}
              value={notes}
              maxLength={2000}
              onChange={(event) => setNotes(event.target.value)}
            />
          </Field>
          <ul className="space-y-2">
            {project.blueprint_versions.map((version) => (
              <li
                key={version.version}
                className="flex flex-wrap items-center gap-3 rounded-lg border border-neutral-800 p-3"
              >
                <span>Version {version.version}</span>
                <span className="workspace-badge">
                  {version.approved ? "Approved" : "Awaiting approval"}
                </span>
                {!version.approved && (
                  <button
                    type="button"
                    className={secondary}
                    disabled={busy || notes.trim().length < 3}
                    onClick={() =>
                      void run(
                        () =>
                          portfolioApi.approve(
                            project.portfolio_project_id,
                            version.version,
                            notes.trim(),
                          ),
                        "Blueprint version approved.",
                      )
                    }
                  >
                    Approve reviewed version
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      {showArchitecture && (
        <div className="space-y-2">
          <h3 className="font-semibold">Recorded architecture</h3>
          {Object.keys(project.architecture).length ? (
            <pre className="max-w-full overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-sm">
              {JSON.stringify(project.architecture, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-neutral-400">
              No architecture has been recorded yet.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export function MilestonesPanel({
  id,
  milestones,
  busy,
  run,
}: PanelProps & { id: string; milestones: Milestone[] }) {
  const [title, setTitle] = useState("");
  const [criterion, setCriterion] = useState("");

  async function addMilestone(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (title.trim().length < 3 || !criterion.trim()) return;
    const saved = await run(
      () =>
        portfolioApi.addMilestone(id, {
          title: title.trim(),
          description: "",
          sequence_order:
            Math.max(
              0,
              ...milestones.map((milestone) => milestone.sequence_order),
            ) + 1,
          acceptance_criteria: [criterion.trim()],
        }),
      "Milestone added.",
    );
    if (saved) {
      setTitle("");
      setCriterion("");
    }
  }

  return (
    <section className="workspace-panel space-y-4">
      <h2 className="text-xl font-semibold">Milestones</h2>
      <form className="space-y-3" onSubmit={addMilestone}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Milestone title">
            <input
              className="workspace-field"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
              minLength={3}
            />
          </Field>
          <Field label="Acceptance criterion">
            <input
              className="workspace-field"
              value={criterion}
              onChange={(event) => setCriterion(event.target.value)}
              required
            />
          </Field>
        </div>
        <button
          className="workspace-button"
          disabled={busy || title.trim().length < 3 || !criterion.trim()}
        >
          Add milestone
        </button>
      </form>
      {milestones.length === 0 && (
        <p className="text-sm text-neutral-400">
          No milestones have been added.
        </p>
      )}
      <ul className="space-y-3">
        {milestones.map((milestone) => (
          <MilestoneItem
            key={milestone.milestone_id}
            milestone={milestone}
            busy={busy}
            run={run}
          />
        ))}
      </ul>
    </section>
  );
}

function MilestoneItem({
  milestone,
  busy,
  run,
}: PanelProps & { milestone: Milestone }) {
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState(milestone.completion_notes ?? "");

  async function complete(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!notes.trim()) return;
    const saved = await run(
      () =>
        portfolioApi.milestoneStatus(
          milestone.milestone_id,
          "completed",
          notes.trim(),
        ),
      "Milestone completion recorded.",
    );
    if (saved) setShowNotes(false);
  }

  return (
    <li className="space-y-2 rounded-lg border border-neutral-800 p-3">
      <p className="font-medium wrap-anywhere">
        {milestone.sequence_order}. {milestone.title}{" "}
        <span className="workspace-badge">
          {displayLabel(milestone.status)}
        </span>
      </p>
      <p className="text-sm wrap-anywhere text-neutral-400">
        {milestone.acceptance_criteria.join(" · ")}
      </p>
      {milestone.status === "completed" &&
        !showNotes &&
        milestone.completion_notes && (
          <p className="text-sm wrap-anywhere">{milestone.completion_notes}</p>
        )}
      {milestone.status !== "completed" && !showNotes && (
        <button
          type="button"
          className={secondary}
          disabled={busy}
          onClick={() => setShowNotes(true)}
        >
          Mark completed
        </button>
      )}
      {showNotes && (
        <form className="space-y-3" onSubmit={complete}>
          <Field label="Acceptance notes">
            <textarea
              className="workspace-field"
              rows={2}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              required
              maxLength={4000}
            />
          </Field>
          <div className="flex flex-wrap gap-2">
            <button
              className="workspace-button"
              disabled={busy || !notes.trim()}
            >
              Record completion
            </button>
            <button
              type="button"
              className={secondary}
              onClick={() => setShowNotes(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </li>
  );
}

export function ArtifactsPanel({
  id,
  artifacts,
  busy,
  run,
}: PanelProps & { id: string; artifacts: Artifact[] }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [artifactType, setArtifactType] = useState("repository");
  const [reviewId, setReviewId] = useState("");
  const selected = artifacts.find(
    (artifact) => artifact.artifact_id === reviewId,
  );

  async function addArtifact(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (title.trim().length < 3) return;
    const saved = await run(
      () =>
        portfolioApi.addArtifact(id, {
          artifact_type: artifactType,
          title: title.trim(),
          content: content.trim(),
        }),
      "Draft artifact saved.",
    );
    if (saved) {
      setTitle("");
      setContent("");
    }
  }

  return (
    <section className="workspace-panel space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Artifacts and evidence</h2>
        <p className="mt-1 text-sm text-neutral-400">
          Review evidence to support claims before you publish them.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {draftKinds.map((kind) => (
          <button
            key={kind}
            type="button"
            className={secondary}
            disabled={busy}
            onClick={() =>
              void run(
                () => portfolioApi.draft(id, kind),
                "Draft created with planned claim scope.",
              )
            }
          >
            Draft {kind.replaceAll("_", " ")}
          </button>
        ))}
      </div>
      <form className="space-y-3" onSubmit={addArtifact}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Artifact type">
            <select
              className="workspace-field"
              value={artifactType}
              onChange={(event) => setArtifactType(event.target.value)}
            >
              {artifactTypes.map((type) => (
                <option key={type} value={type}>
                  {displayLabel(type)}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Artifact title">
            <input
              className="workspace-field"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
              minLength={3}
            />
          </Field>
        </div>
        <Field label="Artifact content or summary">
          <textarea
            className="workspace-field"
            rows={3}
            value={content}
            onChange={(event) => setContent(event.target.value)}
          />
        </Field>
        <button
          className="workspace-button"
          disabled={busy || title.trim().length < 3}
        >
          Add draft artifact
        </button>
      </form>
      {artifacts.length === 0 && (
        <p className="text-sm text-neutral-400">
          No artifacts have been added.
        </p>
      )}
      <ul className="space-y-2">
        {artifacts.map((artifact) => (
          <li
            key={artifact.artifact_id}
            className="space-y-2 rounded-lg border border-neutral-800 p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-medium wrap-anywhere">{artifact.title}</h3>
              <span className="workspace-badge">
                {displayLabel(artifact.claim_scope)}
              </span>
              <span className="workspace-badge">
                {displayLabel(artifact.verification_status)}
              </span>
              <span className="text-sm text-neutral-400">
                v{artifact.version}
              </span>
            </div>
            <p className="max-h-32 overflow-auto whitespace-pre-wrap wrap-anywhere text-neutral-400">
              {artifact.content}
            </p>
            <button
              type="button"
              className={secondary}
              disabled={busy || reviewId === artifact.artifact_id}
              onClick={() => setReviewId(artifact.artifact_id)}
            >
              Review evidence
            </button>
            {selected?.artifact_id === artifact.artifact_id && (
              <ArtifactReview
                key={JSON.stringify([selected.artifact_id, selected.version])}
                artifact={selected}
                busy={busy}
                run={run}
                close={() => setReviewId("")}
              />
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ArtifactReview({
  artifact,
  busy,
  run,
  close,
}: PanelProps & { artifact: Artifact; close: () => void }) {
  const [scope, setScope] = useState(artifact.claim_scope);
  const [status, setStatus] = useState(artifact.verification_status);
  const [evidence, setEvidence] = useState(
    JSON.stringify(artifact.evidence, null, 2),
  );
  const [url, setUrl] = useState(artifact.source_url ?? "");
  const [notes, setNotes] = useState("");

  async function saveReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (notes.trim().length < 3) return;
    const saved = await run(
      async () =>
        portfolioApi.reviewArtifact(artifact.artifact_id, {
          claim_scope: scope,
          verification_status: status,
          evidence: jsonObject(evidence),
          source_url: url.trim() || null,
          review_notes: notes.trim(),
        }),
      "Evidence review saved.",
    );
    if (saved) close();
  }

  return (
    <form
      className="my-3 space-y-3 rounded-lg border border-neutral-700 p-3"
      onSubmit={saveReview}
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Claim scope">
          <select
            className="workspace-field"
            value={scope}
            onChange={(event) => setScope(event.target.value)}
          >
            {claimScopes.map((item) => (
              <option key={item} value={item}>
                {displayLabel(item)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Verification status">
          <select
            className="workspace-field"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            {verificationStatuses.map((item) => (
              <option key={item} value={item}>
                {displayLabel(item)}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Evidence JSON">
        <textarea
          className="workspace-field font-mono"
          rows={5}
          value={evidence}
          onChange={(event) => setEvidence(event.target.value)}
          required
        />
      </Field>
      <Field label="Publication URL">
        <input
          className="workspace-field"
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />
      </Field>
      <Field label="Review notes">
        <textarea
          className="workspace-field"
          rows={2}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          required
          minLength={3}
        />
      </Field>
      <div className="flex flex-wrap gap-2">
        <button
          className="workspace-button"
          disabled={busy || notes.trim().length < 3}
        >
          Save evidence review
        </button>
        <button type="button" className={secondary} onClick={close}>
          Cancel
        </button>
      </div>
    </form>
  );
}

export function PublicationPanel({
  id,
  readiness,
}: {
  id: string;
  readiness: Readiness;
}) {
  const [proposals, setProposals] = useState<unknown[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadProposals() {
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      setProposals(await portfolioApi.evidenceProposals(id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="workspace-panel space-y-4">
      <h2 className="text-xl font-semibold">Publication readiness</h2>
      <ReadinessDetails readiness={readiness} />
      <button
        type="button"
        className={secondary}
        disabled={loading}
        onClick={() => void loadProposals()}
      >
        {loading
          ? "Loading evidence proposals…"
          : "View skill evidence proposals"}
      </button>
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {proposals &&
        (proposals.length === 0 ? (
          <StatusMessage tone="info">
            No skill evidence proposals are available.
          </StatusMessage>
        ) : (
          <pre className="max-w-full overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-sm">
            {JSON.stringify(proposals, null, 2)}
          </pre>
        ))}
    </section>
  );
}

export function ReadinessDetails({ readiness }: { readiness: Readiness }) {
  return (
    <div className="space-y-3">
      <p className="font-semibold">
        {readiness.publication_ready
          ? "Ready to publish"
          : "Publication requirements pending"}
      </p>
      <dl className="grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-neutral-400">Blueprint</dt>
          <dd>
            {readiness.approved_blueprint ? "Approved" : "Awaiting approval"}
          </dd>
        </div>
        <div>
          <dt className="text-neutral-400">Completed milestones</dt>
          <dd>
            {readiness.completed_milestones} of {readiness.milestone_count}
          </dd>
        </div>
        <div>
          <dt className="text-neutral-400">Verified artifacts</dt>
          <dd>{readiness.verified_artifact_count}</dd>
        </div>
      </dl>
      {readiness.missing.length > 0 && (
        <ul className="list-inside list-disc text-sm text-neutral-300">
          {readiness.missing.map((requirement) => (
            <li className="wrap-anywhere" key={requirement}>
              {requirement}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function displayLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/^./, (first) => first.toUpperCase());
}

function jsonObject(value: string): Record<string, unknown> {
  let parsed: unknown;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new Error("Enter valid JSON.");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
    throw new Error("Enter a JSON object.");
  return parsed as Record<string, unknown>;
}
