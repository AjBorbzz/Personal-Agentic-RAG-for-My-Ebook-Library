"use client";

import { useState } from "react";
import { StatusMessage } from "@/components/WorkspaceUI";
import { skillAPI } from "@/lib/skill-intelligence-api";
import type { ViewData } from "./skill-view-data";
import type { ViewAction } from "./skill-view-data";
import {
  LevelSelect,
  SkillSearch,
  SkillStateEditor,
  useSkillSearch,
} from "./SkillEditors";

type Interactive = { profileId: string; busy: boolean; mutate: ViewAction };
const box = "workspace-panel";
const input = "workspace-field";
const btn = "workspace-button";
const subBtn = "workspace-button workspace-button--secondary";
const tag = "workspace-badge";
const num = (value: number | string | null | undefined) =>
  value == null ? "Unknown" : String(value);

export function SkillAssessments({
  data,
  profileId,
  busy,
  mutate,
}: Interactive & { data: ViewData }) {
  const { states = [], levels = [] } = data;
  const [levelId, setLevelId] = useState("");
  const search = useSkillSearch();
  const { selected: selectedSkillId } = search;
  return (
    <div className="space-y-4">
      <section className={box}>
        <h2 className="mb-3 text-xl font-semibold">Track a skill</h2>
        {search.error && (
          <StatusMessage tone="error">{search.error}</StatusMessage>
        )}
        <SkillSearch {...search} busy={busy || search.searching} />
        <label htmlFor="current-proficiency" className="mt-3 block text-sm">
          Current proficiency (human-assessed)
        </label>
        <LevelSelect
          id="current-proficiency"
          levels={levels}
          value={levelId || null}
          onChange={(v) => setLevelId(v ?? "")}
        />
        <button
          className={`${btn} mt-3`}
          disabled={busy || !selectedSkillId}
          onClick={() =>
            void mutate(
              () =>
                skillAPI.saveState(profileId, selectedSkillId, {
                  current_level_id: levelId || null,
                  target_level_id: null,
                  confidence: null,
                  career_priority: 3,
                  learning_status: "not_started",
                  notes: null,
                }),
              "Skill state saved.",
            )
          }
        >
          Track canonical skill
        </button>
        <p className="mt-2 text-sm text-neutral-400">
          Unknown is permitted; never infer a level from AI or a book mapping.
        </p>
      </section>
      {states.map((s) => (
        <SkillStateEditor
          key={JSON.stringify([
            s.profile_skill_id,
            s.current_level_id,
            s.target_level_id,
            s.confidence,
            s.career_priority,
            s.learning_status,
          ])}
          state={s}
          levels={levels}
          busy={busy}
          onSave={async (body) =>
            mutate(
              () => skillAPI.saveState(profileId, s.skill_id, body),
              "Skill state updated.",
            )
          }
        />
      ))}
      {states.length === 0 && (
        <section className={box}>
          No tracked skills. Search the canonical taxonomy above.
        </section>
      )}
    </div>
  );
}

export function SkillEvidence({
  data,
  skillId,
  profileId,
  busy,
  mutate,
}: Interactive & { data: ViewData; skillId: string }) {
  const {
    states = [],
    levels = [],
    gaps,
    recommendations = [],
    evidence = [],
  } = data;
  const [evidenceTitle, setEvidenceTitle] = useState("");
  const [evidenceType, setEvidenceType] = useState("manual");
  const currentState = states.find((state) => state.skill_id === skillId);
  const skillGaps = gaps?.gaps.filter((gap) => gap.skill_id === skillId) ?? [];
  return (
    <div className="space-y-4">
      <section className={box}>
        <h2 className="text-xl font-semibold break-words">
          {skillGaps[0]?.skill_name ?? skillId}
        </h2>
        <p className="mt-2">
          Current:{" "}
          {levels.find((l) => l.level_id === currentState?.current_level_id)
            ?.name ?? "Unknown"}
        </p>
        <p>
          Target:{" "}
          {levels.find((l) => l.level_id === currentState?.target_level_id)
            ?.name ?? "Unset"}
        </p>
        <p>Confidence: {num(currentState?.confidence)}</p>
        {skillGaps.map((g) => (
          <div className="mt-3 space-y-1" key={g.skill_id}>
            <span className={tag}>{g.gap_type}</span>
            <p>{g.explanation}</p>
            <p>Gap steps: {num(g.gap_steps)}</p>
            <p>
              Missing prerequisites:{" "}
              {g.missing_prerequisite_skill_ids.join(", ") || "None"}
            </p>
            <p>Approved supporting books: {g.approved_supporting_book_count}</p>
          </div>
        ))}
        {!currentState && <p>No recorded skill state for this profile.</p>}
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Evidence and review</h2>
        <div className="mt-3 space-y-3">
          {evidence.map((e) => (
            <div
              key={e.evidence_id}
              className="rounded-xl border border-neutral-700 p-3"
            >
              <p className="font-medium">{e.title}</p>
              <span className={tag}>{e.verification_status}</span>
              <p className="text-sm text-neutral-400">{e.description}</p>
              {e.verification_status === "unverified" && (
                <button
                  className={`${subBtn} mt-2`}
                  disabled={busy}
                  onClick={() =>
                    void mutate(
                      () => skillAPI.reviewEvidence(e.evidence_id, "reviewed"),
                      "Evidence marked reviewed. Proficiency was not changed.",
                    )
                  }
                >
                  Mark reviewed
                </button>
              )}
            </div>
          ))}
          {evidence.length === 0 && <p>No evidence linked to this skill.</p>}
        </div>
        <label htmlFor="evidence-title" className="mt-4 block text-sm">
          Evidence title
        </label>
        <input
          id="evidence-title"
          className={input}
          value={evidenceTitle}
          onChange={(e) => setEvidenceTitle(e.target.value)}
        />
        <label htmlFor="evidence-kind" className="mt-3 block text-sm">
          Evidence type
        </label>
        <select
          id="evidence-kind"
          className={input}
          value={evidenceType}
          onChange={(e) => setEvidenceType(e.target.value)}
        >
          {[
            "manual",
            "project",
            "work_experience",
            "certification",
            "course",
            "assessment",
            "repository",
            "exercise",
            "publication",
          ].map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <button
          className={`${btn} mt-3`}
          disabled={busy || !currentState || !evidenceTitle.trim()}
          onClick={() =>
            void mutate(
              () =>
                skillAPI.addEvidence(profileId, skillId, {
                  evidence_type: evidenceType,
                  title: evidenceTitle.trim(),
                }),
              "Evidence added; current level unchanged.",
            )
          }
        >
          Add evidence
        </button>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Related recommendations</h2>
        {recommendations
          .filter((r) => r.skill_id === skillId)
          .map((r) => (
            <p key={r.recommendation_id} className="mt-2">
              {r.title}: {r.explanation}
            </p>
          ))}
      </section>
    </div>
  );
}
