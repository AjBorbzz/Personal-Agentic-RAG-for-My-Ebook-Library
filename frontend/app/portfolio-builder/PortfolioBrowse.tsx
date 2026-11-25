"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import {
  portfolioApi,
  type Opportunity,
  type Profile,
  type Project,
  type Readiness,
  type Target,
} from "@/lib/portfolio-api";
import type { BrowseView } from "./PortfolioWorkspace";
import {
  ReadinessDetails,
  portfolioProjectPath,
} from "./PortfolioProjectSections";

type LoadResult<T> = { data: T } | { error: string };
type Draft = { skillId: string; title: string; slug: string; problem: string };

const slugPattern = "[a-z0-9]+(?:-[a-z0-9]+)*";
const emptyDraft = { skillId: "", title: "", slug: "", problem: "" };

export function PortfolioBrowse({ view }: { view: BrowseView }) {
  const [profiles, setProfiles] = useState<LoadResult<Profile[]> | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string>();

  useEffect(() => {
    const controller = new AbortController();
    portfolioApi.profiles({ signal: controller.signal }).then(
      (data) => {
        if (!controller.signal.aborted) setProfiles({ data });
      },
      (cause) => {
        if (!controller.signal.aborted)
          setProfiles({ error: requestError(cause) });
      },
    );
    return () => controller.abort();
  }, []);

  const rows = profiles && "data" in profiles ? profiles.data : [];
  const profileId =
    selectedProfileId ??
    rows.find((profile) => profile.is_active)?.profile_id ??
    "";

  const [targetResult, setTargetResult] = useState<{
    profileId: string;
    result: LoadResult<Target[]>;
  } | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState<string>();

  useEffect(() => {
    if (!profileId) return;

    const controller = new AbortController();
    portfolioApi.targets(profileId, { signal: controller.signal }).then(
      (data) => {
        if (!controller.signal.aborted) {
          setTargetResult({
            profileId,
            result: {
              data: data.filter((target) => target.status === "active"),
            },
          });
        }
      },
      (cause) => {
        if (!controller.signal.aborted) {
          setTargetResult({
            profileId,
            result: { error: requestError(cause) },
          });
        }
      },
    );
    return () => controller.abort();
  }, [profileId]);

  const targets =
    targetResult?.profileId === profileId ? targetResult.result : null;
  const activeTargets = targets && "data" in targets ? targets.data : [];
  const targetId = selectedTargetId ?? activeTargets[0]?.career_target_id ?? "";

  function changeProfile(id: string) {
    setSelectedProfileId(id);
    setSelectedTargetId(undefined);
  }

  if (!profiles)
    return (
      <StatusMessage tone="info">Loading portfolio profiles…</StatusMessage>
    );
  if ("error" in profiles)
    return <StatusMessage tone="error">{profiles.error}</StatusMessage>;

  return (
    <>
      <section className="workspace-panel grid gap-4 sm:grid-cols-2">
        <Field label="Skill profile">
          <select
            className="workspace-field"
            value={profileId}
            onChange={(event) => changeProfile(event.target.value)}
          >
            <option value="">Select a profile</option>
            {rows.map((profile) => (
              <option key={profile.profile_id} value={profile.profile_id}>
                {profile.profile_name}
              </option>
            ))}
          </select>
        </Field>
        {profileId && (
          <Field label="Active career target">
            <select
              className="workspace-field"
              value={targetId}
              disabled={
                !targets || "error" in targets || activeTargets.length === 0
              }
              onChange={(event) => setSelectedTargetId(event.target.value)}
            >
              <option value="">
                {targets ? "Select a target" : "Loading targets…"}
              </option>
              {activeTargets.map((target) => (
                <option
                  key={target.career_target_id}
                  value={target.career_target_id}
                >
                  {target.role_name}
                </option>
              ))}
            </select>
          </Field>
        )}
        {!profileId && (
          <p className="self-end pb-2 text-sm text-neutral-400">
            {rows.length ? (
              "Choose a profile to view its portfolio."
            ) : (
              <>
                Create a profile in{" "}
                <Link className="underline" href="/skill-intelligence">
                  Skill Intelligence
                </Link>{" "}
                to get started.
              </>
            )}
          </p>
        )}
      </section>
      {profileId && !targets && (
        <StatusMessage tone="info">Loading career targets…</StatusMessage>
      )}
      {targets && "error" in targets && (
        <StatusMessage tone="error">{targets.error}</StatusMessage>
      )}
      {profileId && targets && "data" in targets && (
        <BrowseResults
          key={JSON.stringify([profileId, targetId])}
          view={view}
          profileId={profileId}
          targetId={targetId}
        />
      )}
    </>
  );
}

function BrowseResults({
  view,
  profileId,
  targetId,
}: {
  view: BrowseView;
  profileId: string;
  targetId: string;
}) {
  const [opportunities, setOpportunities] = useState<LoadResult<
    Opportunity[]
  > | null>(null);
  const [projects, setProjects] = useState<LoadResult<Project[]> | null>(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const formTitle = useRef<HTMLHeadingElement>(null);
  const scope = useRef<AbortSignal>(null);
  const router = useRouter();

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    scope.current = controller.signal;

    if (view !== "new") {
      portfolioApi.projects(profileId, targetId || undefined, options).then(
        (data) => {
          if (!controller.signal.aborted) setProjects({ data });
        },
        (cause) => {
          if (!controller.signal.aborted)
            setProjects({ error: requestError(cause) });
        },
      );
    }
    if (targetId && view !== "readiness") {
      portfolioApi.opportunities(profileId, targetId, options).then(
        (data) => {
          if (!controller.signal.aborted) setOpportunities({ data });
        },
        (cause) => {
          if (!controller.signal.aborted)
            setOpportunities({ error: requestError(cause) });
        },
      );
    }
    return () => controller.abort();
  }, [profileId, targetId, view]);

  const gaps =
    opportunities && "data" in opportunities ? opportunities.data : [];
  const existingProjects = projects && "data" in projects ? projects.data : [];

  function fillDraft(gap: Opportunity) {
    const slug = gap.skill_name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    setDraft({
      skillId: gap.skill_id,
      title: gap.title_suggestion,
      slug: slug ? `${slug}-portfolio` : "skill-portfolio",
      problem: `Demonstrate ${gap.skill_name} with a testable, evidence-backed application.`,
    });
    formTitle.current?.focus();
  }

  async function createProject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = draft.title.trim();
    const slug = draft.slug.trim();
    const problem = draft.problem.trim();
    if (creating || !targetId || !draft.skillId) return;
    if (
      title.length < 3 ||
      !new RegExp(`^${slugPattern}$`).test(slug) ||
      slug.length < 3 ||
      problem.length < 10
    ) {
      setError(
        "Enter a project title, a slug using lowercase letters or numbers, and a problem statement of at least 10 characters.",
      );
      return;
    }

    const signal = scope.current;
    if (!signal || signal.aborted) return;
    setCreating(true);
    setError("");
    try {
      const project = await portfolioApi.create({
        profile_id: profileId,
        career_target_id: targetId,
        title,
        slug,
        problem_statement: problem,
        target_skill_ids: [draft.skillId],
      });
      if (!signal.aborted)
        router.push(portfolioProjectPath(project.portfolio_project_id));
    } catch (cause) {
      if (!signal.aborted) {
        setError(requestError(cause));
        setCreating(false);
      }
    }
  }

  return (
    <>
      {view !== "readiness" && !targetId && (
        <StatusMessage tone="info">
          Choose an active career target to see portfolio opportunities.
        </StatusMessage>
      )}
      {view !== "readiness" && targetId && !opportunities && (
        <StatusMessage tone="info">Loading opportunities…</StatusMessage>
      )}
      {opportunities && "error" in opportunities && (
        <StatusMessage tone="error">{opportunities.error}</StatusMessage>
      )}
      {(view === "dashboard" || view === "opportunities") &&
        opportunities &&
        "data" in opportunities && (
          <section className="workspace-panel grid gap-3">
            <h2 className="text-xl font-semibold">Actionable skill gaps</h2>
            {gaps.length === 0 && (
              <p className="text-neutral-400">
                No actionable gaps were found for this target.
              </p>
            )}
            {gaps.map((gap) => (
              <article
                key={gap.skill_id}
                className="min-w-0 space-y-2 rounded-lg border border-neutral-800 p-4"
              >
                <h3 className="font-semibold wrap-anywhere">
                  {gap.skill_name}{" "}
                  <span className="workspace-badge">
                    {gap.gap_type.replaceAll("_", " ")}
                  </span>
                </h3>
                <p className="text-sm text-neutral-400">{gap.explanation}</p>
                <p className="text-sm">
                  Trusted books{" "}
                  <strong>{gap.source_document_ids.length}</strong>
                </p>
                {gap.no_trusted_book_sources && (
                  <p className="text-sm text-neutral-400">
                    No approved sources available.
                  </p>
                )}
                <button
                  type="button"
                  className="workspace-button workspace-button--secondary"
                  onClick={() => fillDraft(gap)}
                >
                  Use for new project
                </button>
              </article>
            ))}
          </section>
        )}
      {view !== "readiness" && targetId && gaps.length > 0 && (
        <section id="create" className="workspace-panel">
          <h2 className="text-xl font-semibold" ref={formTitle} tabIndex={-1}>
            Create a project idea
          </h2>
          {error && (
            <div className="mt-3">
              <StatusMessage tone="error">{error}</StatusMessage>
            </div>
          )}
          <form className="mt-4 space-y-3" onSubmit={createProject}>
            <Field label="Target skill">
              <select
                className="workspace-field"
                value={draft.skillId}
                required
                onChange={(event) =>
                  setDraft({ ...draft, skillId: event.target.value })
                }
              >
                <option value="">Select a skill gap</option>
                {gaps.map((gap) => (
                  <option key={gap.skill_id} value={gap.skill_id}>
                    {gap.skill_name}
                  </option>
                ))}
              </select>
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Project title">
                <input
                  className="workspace-field"
                  value={draft.title}
                  required
                  minLength={3}
                  maxLength={240}
                  onChange={(event) =>
                    setDraft({ ...draft, title: event.target.value })
                  }
                />
              </Field>
              <Field
                label="Project slug"
                hint="Use lowercase letters, numbers, and hyphens."
              >
                <input
                  className="workspace-field"
                  value={draft.slug}
                  required
                  minLength={3}
                  maxLength={160}
                  pattern={slugPattern}
                  onChange={(event) =>
                    setDraft({ ...draft, slug: event.target.value })
                  }
                />
              </Field>
            </div>
            <Field label="Problem statement">
              <textarea
                className="workspace-field"
                rows={3}
                value={draft.problem}
                required
                minLength={10}
                onChange={(event) =>
                  setDraft({ ...draft, problem: event.target.value })
                }
              />
            </Field>
            <button className="workspace-button" disabled={creating}>
              {creating ? "Creating project…" : "Create project idea"}
            </button>
          </form>
        </section>
      )}
      {view === "new" &&
        opportunities &&
        "data" in opportunities &&
        gaps.length === 0 && (
          <StatusMessage tone="info">
            There are no actionable gaps to base a new project on for this
            target.
          </StatusMessage>
        )}
      {view !== "new" && !projects && (
        <StatusMessage tone="info">Loading portfolio projects…</StatusMessage>
      )}
      {projects && "error" in projects && (
        <StatusMessage tone="error">{projects.error}</StatusMessage>
      )}
      {projects &&
        "data" in projects &&
        (view === "readiness" ? (
          <ReadinessIndex projects={existingProjects} />
        ) : (
          <section className="workspace-panel">
            <h2 className="text-xl font-semibold">Existing projects</h2>
            {existingProjects.length === 0 ? (
              <p className="mt-2 text-neutral-400">
                No projects match this selection.
              </p>
            ) : (
              <ul className="mt-3 divide-y divide-neutral-800">
                {existingProjects.map((project) => (
                  <li
                    key={project.portfolio_project_id}
                    className="flex flex-wrap items-center justify-between gap-2 py-3"
                  >
                    <Link
                      className="min-w-0 font-medium wrap-anywhere underline"
                      href={portfolioProjectPath(project.portfolio_project_id)}
                    >
                      {project.title}
                    </Link>
                    <span className="workspace-badge">
                      {project.status.replaceAll("_", " ")}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
    </>
  );
}

function ReadinessIndex({ projects }: { projects: Project[] }) {
  const [selectedId, setSelectedId] = useState("");
  if (!projects.length)
    return (
      <StatusMessage tone="info">
        No projects match this selection.
      </StatusMessage>
    );

  return (
    <section className="workspace-panel space-y-4">
      <Field label="Project to review">
        <select
          className="workspace-field"
          value={selectedId}
          onChange={(event) => setSelectedId(event.target.value)}
        >
          <option value="">Select a project</option>
          {projects.map((project) => (
            <option
              key={project.portfolio_project_id}
              value={project.portfolio_project_id}
            >
              {project.title}
            </option>
          ))}
        </select>
      </Field>
      {selectedId && <ReadinessPreview key={selectedId} id={selectedId} />}
    </section>
  );
}

function ReadinessPreview({ id }: { id: string }) {
  const [readiness, setReadiness] = useState<LoadResult<Readiness> | null>(
    null,
  );

  useEffect(() => {
    const controller = new AbortController();
    portfolioApi.readiness(id, { signal: controller.signal }).then(
      (data) => {
        if (!controller.signal.aborted) setReadiness({ data });
      },
      (cause) => {
        if (!controller.signal.aborted)
          setReadiness({ error: requestError(cause) });
      },
    );
    return () => controller.abort();
  }, [id]);

  if (!readiness)
    return (
      <StatusMessage tone="info">Checking publication readiness…</StatusMessage>
    );
  if ("error" in readiness)
    return <StatusMessage tone="error">{readiness.error}</StatusMessage>;
  return (
    <div className="space-y-4">
      <ReadinessDetails readiness={readiness.data} />
      <Link
        className="workspace-button workspace-button--secondary"
        href={portfolioProjectPath(id)}
      >
        Open project workspace
      </Link>
    </div>
  );
}

function requestError(cause: unknown) {
  return cause instanceof Error ? cause.message : String(cause);
}
