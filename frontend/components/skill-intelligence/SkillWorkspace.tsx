"use client";

import { useEffect, useState } from "react";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { SectionNav, StatusMessage } from "@/components/WorkspaceUI";
import { skillAPI } from "@/lib/skill-intelligence-api";
import { CareerTarget, CareerTargets } from "./CareerTargets";
import { ReadingQueue, Recommendations } from "./LearningActions";
import { SkillAssessments, SkillEvidence } from "./SkillAssessments";
import { SkillOverview } from "./SkillOverview";
import { useSkillProfiles } from "./SkillProfiles";
import {
  loadView,
  type Mode,
  type Props,
  type ViewData,
} from "./skill-view-data";

type ViewResult = {
  targetFilter: string;
  revision: number;
  value?: ViewData;
  error?: string;
};

const NAV = [
  { label: "Overview", href: "/skill-intelligence" },
  { label: "My skills", href: "/skill-intelligence/profile" },
  { label: "Career targets", href: "/skill-intelligence/career-targets" },
  { label: "Recommendations", href: "/skill-intelligence/recommendations" },
  { label: "Reading queue", href: "/skill-intelligence/reading-queue" },
] as const;

const HEADERS: Record<Mode, { title: string; description: string }> = {
  overview: {
    title: "Skill Intelligence",
    description:
      "Review your assessed skills, career targets, and next steps from the ebook library.",
  },
  profile: {
    title: "My skills",
    description:
      "Track canonical skills and record your own proficiency assessments.",
  },
  skill: {
    title: "Skill evidence",
    description: "Review the assessment, gaps, and evidence for this skill.",
  },
  targets: {
    title: "Career targets",
    description:
      "Define roles and compare their requirements with your current skills.",
  },
  target: {
    title: "Career target",
    description:
      "Review required proficiency and see where your skill profile falls short.",
  },
  recommendations: {
    title: "Skill recommendations",
    description:
      "Find learning actions grounded in your skill gaps and trusted ebook sources.",
  },
  queue: {
    title: "Reading queue",
    description:
      "Plan reading and track progress on your accepted learning actions.",
  },
};

const box = "workspace-panel";
const input = "workspace-field";
const btn = "workspace-button";
const errorText = (error: unknown) =>
  error instanceof Error ? error.message : String(error);

export default function SkillWorkspace(props: Props) {
  const {
    profiles,
    activeProfiles,
    profileId,
    loadError,
    selectProfile,
    addProfile,
  } = useSkillProfiles();
  const [profileName, setProfileName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function createProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = profileName.trim();
    if (!name || busy) return;

    setBusy(true);
    setError("");
    setNotice("");
    try {
      const profile = await skillAPI.createProfile({
        profile_name: name,
        is_default: profiles?.length === 0,
      });
      addProfile(profile);
      setProfileName("");
      setNotice("Profile created.");
    } catch (cause) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageFrame width="wide" className="space-y-5">
      <PageHeader
        {...HEADERS[props.mode]}
        eyebrow={props.mode === "overview" ? "Learning" : "Skill Intelligence"}
        back={
          props.mode === "target"
            ? {
                label: "Career targets",
                href: "/skill-intelligence/career-targets",
              }
            : props.mode === "skill"
              ? { label: "My skills", href: "/skill-intelligence/profile" }
              : undefined
        }
      />
      <SectionNav label="Skill intelligence sections" items={NAV} />
      {(error || loadError) && (
        <StatusMessage tone="error">{error || loadError}</StatusMessage>
      )}
      {notice && <StatusMessage tone="success">{notice}</StatusMessage>}
      {!profiles && !loadError && (
        <StatusMessage tone="info">Loading skill profiles…</StatusMessage>
      )}
      {profiles && !profileId && (
        <section className={box}>
          <h2 className="text-xl font-semibold">Create a skill profile</h2>
          <p className="mt-1 text-neutral-400">
            A profile keeps your assessments, goals, and reading queue together.
          </p>
          <form className="mt-4 max-w-lg space-y-3" onSubmit={createProfile}>
            <label htmlFor="new-profile" className="block text-sm">
              Profile name
            </label>
            <input
              id="new-profile"
              className={input}
              value={profileName}
              onChange={(event) => setProfileName(event.target.value)}
              required
            />
            <button className={btn} disabled={busy || !profileName.trim()}>
              {busy ? "Creating profile…" : "Create profile"}
            </button>
          </form>
        </section>
      )}
      {profileId && (
        <>
          <section className={box}>
            <label className="block text-sm" htmlFor="profile-selector">
              Active profile
            </label>
            <select
              id="profile-selector"
              className={`${input} mt-2 max-w-lg`}
              value={profileId}
              onChange={(event) => {
                selectProfile(event.target.value);
                setNotice("");
              }}
            >
              {activeProfiles.map((profile) => (
                <option key={profile.profile_id} value={profile.profile_id}>
                  {profile.profile_name}
                  {profile.is_default ? " (default)" : ""}
                </option>
              ))}
            </select>
          </section>
          <SkillView
            key={JSON.stringify([
              profileId,
              props.mode,
              props.skillId,
              props.targetId,
            ])}
            {...props}
            profileId={profileId}
          />
        </>
      )}
    </PageFrame>
  );
}

function SkillView({
  mode,
  skillId,
  targetId,
  profileId,
}: Props & { profileId: string }) {
  const [selectedTargetId, setSelectedTargetId] = useState("");
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<ViewResult | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [mutating, setMutating] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const scope = { targetFilter: selectedTargetId, revision };
    loadView(
      { mode, skillId, targetId },
      profileId,
      selectedTargetId,
      controller.signal,
    )
      .then((value) => {
        if (!controller.signal.aborted) setResult({ ...scope, value });
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setResult((previous) => ({
          ...scope,
          value: previous?.value,
          error: errorText(cause),
        }));
      });
    return () => controller.abort();
  }, [mode, profileId, revision, selectedTargetId, skillId, targetId]);

  const loading =
    result?.targetFilter !== selectedTargetId || result.revision !== revision;
  const busy = mutating || loading;
  const recommendationsLoaded = !loading && !result?.error;

  function changeTarget(nextTargetId: string) {
    setSelectedTargetId(nextTargetId);
    setError("");
    setSuccess("");
  }

  async function mutate(action: () => Promise<unknown>, message: string) {
    if (busy) return;
    setMutating(true);
    setError("");
    setSuccess("");
    try {
      await action();
      setSuccess(message);
      setRevision((value) => value + 1);
    } catch (cause) {
      setError(errorText(cause));
    } finally {
      setMutating(false);
    }
  }

  function renderView(data: ViewData) {
    const actions = { profileId, busy, mutate };
    switch (mode) {
      case "overview":
        return <SkillOverview {...data} />;
      case "profile":
        return <SkillAssessments data={data} {...actions} />;
      case "skill":
        return (
          skillId && (
            <SkillEvidence data={data} skillId={skillId} {...actions} />
          )
        );
      case "targets":
        return <CareerTargets data={data} {...actions} />;
      case "target":
        return (
          targetId && (
            <CareerTarget
              data={data}
              targetId={targetId}
              busy={busy}
              mutate={mutate}
            />
          )
        );
      case "recommendations":
        return (
          <Recommendations
            data={data}
            {...actions}
            selectedTargetId={selectedTargetId}
            changeTarget={changeTarget}
            recommendationsLoaded={recommendationsLoaded}
          />
        );
      case "queue":
        return <ReadingQueue data={data} busy={busy} mutate={mutate} />;
    }
  }

  return (
    <div className="min-w-0 space-y-4" aria-busy={busy}>
      {loading && (
        <StatusMessage tone="info">Loading workspace data…</StatusMessage>
      )}
      {(error || (!loading && result?.error)) && (
        <StatusMessage tone="error">{error || result?.error}</StatusMessage>
      )}
      {success && <StatusMessage tone="success">{success}</StatusMessage>}
      {result?.value && renderView(result.value)}
    </div>
  );
}
