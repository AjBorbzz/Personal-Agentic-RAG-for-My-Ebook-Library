"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { skillAPI } from "@/lib/skill-intelligence-api";
import type {
  CanonicalSkill,
  ProficiencyLevel,
  QueueItem,
  SkillState,
} from "@/lib/skill-intelligence-types";

export function LevelSelect({
  levels,
  value,
  onChange,
  includeUnknown = true,
  id,
}: {
  id: string;
  levels: ProficiencyLevel[];
  value: string | null;
  onChange: (v: string | null) => void;
  includeUnknown?: boolean;
}) {
  return (
    <select
      id={id}
      className="workspace-field"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
    >
      {includeUnknown && <option value="">Unknown / unset</option>}
      {levels.map((l) => (
        <option key={l.level_id} value={l.level_id}>
          {l.name} ({l.code})
        </option>
      ))}
    </select>
  );
}

export function useSkillSearch() {
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState<CanonicalSkill[]>([]);
  const [selected, setSelected] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const searchRequest = useRef<AbortController | null>(null);

  useEffect(() => () => searchRequest.current?.abort(), []);

  function onQuery(nextQuery: string) {
    searchRequest.current?.abort();
    setQuery(nextQuery);
    setSearching(false);
    setError("");
    setOptions([]);
    setSelected("");
  }

  async function onSearch() {
    const controller = new AbortController();
    searchRequest.current?.abort();
    searchRequest.current = controller;
    setSearching(true);
    setError("");
    try {
      const matches = await skillAPI.skills(query.trim(), {
        signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      setOptions(matches);
      setSelected((value) =>
        matches.some((option) => option.skill_id === value) ? value : "",
      );
    } catch (cause) {
      if (!controller.signal.aborted)
        setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      if (!controller.signal.aborted) setSearching(false);
    }
  }

  return {
    query,
    options,
    selected,
    searching,
    error,
    onQuery,
    onSearch,
    onSelected: setSelected,
  };
}

export function SkillSearch({
  query,
  onQuery,
  options,
  selected,
  onSelected,
  busy,
  onSearch,
}: {
  query: string;
  onQuery: (value: string) => void;
  options: CanonicalSkill[];
  selected: string;
  onSelected: (value: string) => void;
  busy: boolean;
  onSearch: () => void;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor="skill-query" className="block text-sm">
        Find canonical skill
      </label>
      <div className="flex flex-wrap gap-2">
        <input
          id="skill-query"
          className="workspace-field min-w-0 flex-1"
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Search skill name or alias"
        />
        <button
          type="button"
          className="workspace-button workspace-button--secondary"
          disabled={busy || !query.trim()}
          onClick={onSearch}
        >
          Search
        </button>
      </div>
      <select
        aria-label="Canonical skill"
        className="workspace-field"
        value={selected}
        onChange={(e) => onSelected(e.target.value)}
      >
        <option value="">Select a canonical skill</option>
        {options.map((sk) => (
          <option key={sk.skill_id} value={sk.skill_id}>
            {sk.name}
          </option>
        ))}
      </select>
    </div>
  );
}

// Keep form draft state local and isolated per skill; this prevents edits from leaking
// from one tracked skill to another when switching profiles.
export function SkillStateEditor({
  state,
  levels,
  busy,
  onSave,
}: {
  state: SkillState;
  levels: ProficiencyLevel[];
  busy: boolean;
  onSave: (body: Partial<SkillState>) => Promise<void>;
}) {
  const [current, setCurrent] = useState(state.current_level_id ?? "");
  const [target, setTarget] = useState(state.target_level_id ?? "");
  const [confidence, setConfidence] = useState(
    state.confidence == null ? "" : String(state.confidence),
  );
  const [priority, setPriority] = useState(state.career_priority);
  const [status, setStatus] = useState(state.learning_status);
  const validConfidence =
    confidence === "" ||
    (Number.isFinite(Number(confidence)) &&
      Number(confidence) >= 0 &&
      Number(confidence) <= 1);
  return (
    <section className="workspace-panel">
      <Link
        className="font-medium break-all underline"
        href={`/skill-intelligence/skills/${encodeURIComponent(
          state.skill_id,
        )}`}
      >
        {state.skill_id}
      </Link>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <label className="text-sm">
          Current level
          <select
            className="workspace-field mt-1"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          >
            <option value="">Unknown</option>
            {levels.map((l) => (
              <option key={l.level_id} value={l.level_id}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Target level
          <select
            className="workspace-field mt-1"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="">Unset</option>
            {levels.map((l) => (
              <option key={l.level_id} value={l.level_id}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Confidence (0–1; blank unknown)
          <input
            className="workspace-field mt-1"
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={confidence}
            onChange={(e) => setConfidence(e.target.value)}
          />
        </label>
        <label className="text-sm">
          Career priority (1–5)
          <input
            className="workspace-field mt-1"
            type="number"
            min="1"
            max="5"
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
          />
        </label>
        <label className="text-sm">
          Learning status
          <select
            className="workspace-field mt-1"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            {[
              "not_started",
              "planned",
              "learning",
              "practicing",
              "demonstrated",
              "maintained",
              "paused",
            ].map((st) => (
              <option key={st}>{st}</option>
            ))}
          </select>
        </label>
      </div>
      <button
        className="workspace-button mt-4"
        disabled={busy || !validConfidence || priority < 1 || priority > 5}
        onClick={() =>
          void onSave({
            current_level_id: current || null,
            target_level_id: target || null,
            confidence: confidence ? Number(confidence) : null,
            career_priority: priority,
            learning_status: status,
            notes: state.notes,
          })
        }
      >
        Save skill assessment
      </button>
    </section>
  );
}

export function QueueEditor({
  item,
  busy,
  onSave,
}: {
  item: QueueItem;
  busy: boolean;
  onSave: (body: {
    status?: QueueItem["status"];
    progress_percent?: number;
    notes?: string;
    priority?: number;
    planned_start?: string | null;
    target_finish?: string | null;
  }) => Promise<void>;
}) {
  const [progress, setProgress] = useState(item.progress_percent);
  const [notes, setNotes] = useState(item.notes ?? "");
  const [start, setStart] = useState(item.planned_start ?? "");
  const [finish, setFinish] = useState(item.target_finish ?? "");
  return (
    <section className="workspace-panel">
      <p className="font-medium break-all">
        {item.document_id
          ? `Book ${item.document_id}`
          : `Skill ${item.skill_id ?? "action"}`}
      </p>
      <p className="text-sm text-neutral-400">
        {item.status}; priority {item.priority}
      </p>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <label className="text-sm">
          Progress (manual %)
          <input
            className="workspace-field mt-1"
            type="number"
            min="0"
            max="100"
            value={progress}
            onChange={(e) => setProgress(Number(e.target.value))}
          />
        </label>
        <label className="text-sm">
          Start date
          <input
            type="date"
            className="workspace-field mt-1"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label className="text-sm">
          Target finish
          <input
            type="date"
            className="workspace-field mt-1"
            value={finish}
            onChange={(e) => setFinish(e.target.value)}
          />
        </label>
      </div>
      <label className="mt-3 block text-sm">
        Notes
        <textarea
          className="workspace-field mt-1"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="workspace-button"
          disabled={
            busy ||
            progress < 0 ||
            progress > 100 ||
            !!(start && finish && finish < start)
          }
          onClick={() =>
            void onSave({
              progress_percent: progress,
              notes,
              planned_start: start || null,
              target_finish: finish || null,
            })
          }
        >
          Save progress
        </button>
        {item.status === "queued" && (
          <button
            className="workspace-button workspace-button--secondary"
            disabled={busy}
            onClick={() => void onSave({ status: "active" })}
          >
            Start
          </button>
        )}
        {item.status === "active" && (
          <button
            className="workspace-button workspace-button--secondary"
            disabled={busy}
            onClick={() => void onSave({ status: "paused" })}
          >
            Pause
          </button>
        )}
        {(item.status === "active" || item.status === "paused") && (
          <button
            className="workspace-button workspace-button--secondary"
            disabled={busy}
            onClick={() =>
              void onSave({ status: "completed", progress_percent: 100 })
            }
          >
            Mark completed
          </button>
        )}
      </div>
    </section>
  );
}
