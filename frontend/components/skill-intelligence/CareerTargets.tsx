"use client";

import Link from "next/link";
import { useState } from "react";
import { StatusMessage } from "@/components/WorkspaceUI";
import { skillAPI } from "@/lib/skill-intelligence-api";
import type { ViewData } from "./skill-view-data";
import type { ViewAction } from "./skill-view-data";
import { LevelSelect, SkillSearch, useSkillSearch } from "./SkillEditors";

type Interactive = { profileId: string; busy: boolean; mutate: ViewAction };
const box = "workspace-panel";
const input = "workspace-field";
const btn = "workspace-button";

export function CareerTargets({
  data,
  profileId,
  busy,
  mutate,
}: Interactive & { data: ViewData }) {
  const { targets = [] } = data;
  const [roleName, setRoleName] = useState("");
  const [roleSlug, setRoleSlug] = useState("");
  const [priority, setPriority] = useState(3);
  return (
    <div className="space-y-4">
      <section className={box}>
        <h2 className="text-xl font-semibold">Create career target</h2>
        <label htmlFor="role-name" className="mt-3 block text-sm">
          Role name
        </label>
        <input
          id="role-name"
          className={input}
          value={roleName}
          onChange={(e) => setRoleName(e.target.value)}
        />
        <label htmlFor="role-slug" className="mt-3 block text-sm">
          Unique role slug
        </label>
        <input
          id="role-slug"
          className={input}
          value={roleSlug}
          onChange={(e) => setRoleSlug(e.target.value)}
        />
        <label htmlFor="role-priority" className="mt-3 block text-sm">
          Priority (1–5)
        </label>
        <input
          id="role-priority"
          className={input}
          type="number"
          min={1}
          max={5}
          value={priority}
          onChange={(e) => setPriority(Number(e.target.value))}
        />
        <button
          className={`${btn} mt-3`}
          disabled={
            busy ||
            !roleName.trim() ||
            !roleSlug.trim() ||
            priority < 1 ||
            priority > 5
          }
          onClick={() =>
            void mutate(
              () =>
                skillAPI.createTarget({
                  profile_id: profileId,
                  role_name: roleName.trim(),
                  role_slug: roleSlug.trim(),
                  priority,
                  status: "exploring",
                }),
              "Career target created.",
            )
          }
        >
          Create target
        </button>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Saved career targets</h2>
        <div className="mt-3 space-y-3">
          {targets.map((t) => (
            <div
              key={t.career_target_id}
              className="rounded-xl border border-neutral-800 p-3"
            >
              <Link
                className="font-medium underline"
                href={`/skill-intelligence/career-targets/${t.career_target_id}`}
              >
                {t.role_name}
              </Link>
              <p className="text-sm text-neutral-400">
                {t.status} · priority {t.priority}
              </p>
            </div>
          ))}
          {targets.length === 0 && <p>No career targets.</p>}
        </div>
      </section>
    </div>
  );
}

export function CareerTarget({
  data,
  targetId,
  busy,
  mutate,
}: Omit<Interactive, "profileId"> & { data: ViewData; targetId: string }) {
  const { target: selectedTarget, requirements = [], gaps, levels = [] } = data;
  const [levelId, setLevelId] = useState("");
  const search = useSkillSearch();
  const { selected: selectedSkillId } = search;
  return (
    <div className="space-y-4">
      <section className={box}>
        <h2 className="text-xl font-semibold">
          {selectedTarget?.role_name ?? "Career target"}
        </h2>
        <p>Status: {selectedTarget?.status ?? "Loading"}</p>
        <p>Requirements: {requirements.length}</p>
        <div className="mt-3 space-y-2">
          {requirements.map((r) => (
            <div
              className="rounded-xl border border-neutral-800 p-3"
              key={r.career_target_skill_id}
            >
              <p>
                {r.skill_id} · required level:{" "}
                {levels.find((l) => l.level_id === r.required_level_id)?.name ??
                  r.required_level_id}
              </p>
              <p className="text-sm text-neutral-400">
                Importance: {r.importance_weight};{" "}
                {r.is_required ? "required" : "optional"}
              </p>
            </div>
          ))}
        </div>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Add or update required skill</h2>
        {search.error && (
          <StatusMessage tone="error">{search.error}</StatusMessage>
        )}
        <SkillSearch {...search} busy={busy || search.searching} />
        <label htmlFor="required-proficiency" className="mt-3 block text-sm">
          Required canonical proficiency level
        </label>
        <LevelSelect
          id="required-proficiency"
          levels={levels}
          value={levelId || null}
          onChange={(v) => setLevelId(v ?? "")}
          includeUnknown={false}
        />
        <button
          className={`${btn} mt-3`}
          disabled={busy || !selectedSkillId || !levelId}
          onClick={() =>
            void mutate(
              () =>
                skillAPI.saveRequirement(targetId, selectedSkillId, {
                  required_level_id: levelId,
                  importance_weight: 3,
                  is_required: true,
                }),
              "Requirement saved.",
            )
          }
        >
          Save requirement
        </button>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Deterministic role gaps</h2>
        {(gaps?.gaps ?? []).map((g) => (
          <div
            className="mt-3 rounded-xl border border-neutral-800 p-3"
            key={g.skill_id}
          >
            <Link
              className="underline"
              href={`/skill-intelligence/skills/${encodeURIComponent(
                g.skill_id,
              )}`}
            >
              {g.skill_name}
            </Link>
            <p>
              {g.gap_type} ·{" "}
              {g.gap_steps == null
                ? "unknown current"
                : `${g.gap_steps} level steps`}
            </p>
            <p className="text-sm text-neutral-400">{g.explanation}</p>
          </div>
        ))}
        {gaps?.gaps.length === 0 && <p>No gaps for this target.</p>}
      </section>
    </div>
  );
}
