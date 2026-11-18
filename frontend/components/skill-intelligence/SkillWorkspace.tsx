"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { skillAPI } from "../../lib/skill-intelligence-api";
import type {
  CanonicalSkill, CareerTarget, CareerTargetSkill, Evidence, GapResponse,
  Profile, ProficiencyLevel, QueueItem, Recommendation, SkillState,
} from "../../lib/skill-intelligence-types";

type Mode = "overview" | "profile" | "skill" | "targets" | "target" | "recommendations" | "queue";
type Props = { mode: Mode; skillId?: string; targetId?: string };
const NAV = [
  ["Overview", "/skill-intelligence"],
  ["My skills", "/skill-intelligence/profile"],
  ["Career targets", "/skill-intelligence/career-targets"],
  ["Recommendations", "/skill-intelligence/recommendations"],
  ["Reading queue", "/skill-intelligence/reading-queue"],
] as const;
const box = "rounded-2xl border border-neutral-800 bg-neutral-900 p-5";
const input = "w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2 text-neutral-100 focus:outline-none focus:ring-2 focus:ring-neutral-400";
const btn = "rounded-lg bg-white px-3 py-2 font-medium text-neutral-950 disabled:cursor-not-allowed disabled:opacity-40";
const subBtn = "rounded-lg border border-neutral-700 px-3 py-2 text-neutral-100 disabled:opacity-40";
const tag = "rounded-md bg-neutral-800 px-2 py-1 text-xs text-neutral-200";
const num = (v: number | string | null | undefined): string => v == null ? "Unknown" : String(v);

export default function SkillWorkspace({mode, skillId, targetId}: Props) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileId, setProfileId] = useState("");
  const [states, setStates] = useState<SkillState[]>([]);
  const [levels, setLevels] = useState<ProficiencyLevel[]>([]);
  const [targets, setTargets] = useState<CareerTarget[]>([]);
  const [selectedTargetId, setSelectedTargetId] = useState("");
  const [requirements, setRequirements] = useState<CareerTargetSkill[]>([]);
  const [gaps, setGaps] = useState<GapResponse | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [skillQuery, setSkillQuery] = useState("");
  const [skillOptions, setSkillOptions] = useState<CanonicalSkill[]>([]);
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [levelId, setLevelId] = useState("");
  const [evidenceTitle, setEvidenceTitle] = useState("");
  const [evidenceType, setEvidenceType] = useState("manual");
  const [newProfileName, setNewProfileName] = useState("");
  const [roleName, setRoleName] = useState("");
  const [roleSlug, setRoleSlug] = useState("");
  const [priority, setPriority] = useState(3);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadProfiles = useCallback(async () => {
    const data = await skillAPI.profiles();
    setProfiles(data);
    setProfileId(old => data.some(p => p.profile_id === old) ? old :
      (data.find(p => p.is_default && p.is_active) ?? data.find(p => p.is_active))?.profile_id ?? "");
  }, []);

  useEffect(() => {
    let live = true;
    Promise.all([skillAPI.profiles(), skillAPI.levels()])
      .then(([p, l]) => { if (!live) return;
        setProfiles(p); setLevels(l);
        setProfileId((p.find(x => x.is_default && x.is_active) ?? p.find(x => x.is_active))?.profile_id ?? "");
      })
      .catch(e => { if (live) setError(String(e)); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, []);

  const refresh = useCallback(async (profile: string, target: string) => {
    const [s, t, g, r, qu] = await Promise.all([
      skillAPI.states(profile), skillAPI.targets(profile),
      skillAPI.gaps(profile, target || undefined),
      skillAPI.recommendations(profile, target || undefined),
      skillAPI.queue(profile),
    ]);
    setStates(s); setTargets(t); setGaps(g); setRecommendations(r); setQueue(qu);
  }, []);

  useEffect(() => {
    if (!profileId) return;
    let live = true;
    setLoading(true);
    const scopedTarget = targetId ?? selectedTargetId;
    // A target URL may belong to a different profile; validate ownership in this page.
    refresh(profileId, scopedTarget).catch(e => { if (live) setError(String(e)); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [profileId, selectedTargetId, targetId, refresh]);

  useEffect(() => {
    if (targetId && targets.length && !targets.some(t => t.career_target_id === targetId)) {
      setError("This career target does not belong to the selected profile.");
    }
  }, [targetId, targets]);

  useEffect(() => {
    if (!profileId || !skillId || mode !== "skill") return;
    skillAPI.evidence(profileId, skillId).then(setEvidence).catch(e => setError(String(e)));
  }, [profileId, skillId, mode]);

  useEffect(() => {
    if (!profileId || !targetId || mode !== "target") return;
    skillAPI.requirements(profileId, targetId).then(setRequirements).catch(e => setError(String(e)));
  }, [profileId, targetId, mode]);

  async function mutate(action: () => Promise<unknown>, message: string, opts?: { reloadEvidence?: boolean; reloadRequirements?: boolean }) {
    setBusy(true); setError(""); setSuccess("");
    try {
      await action();
      if (profileId) await refresh(profileId, targetId ?? selectedTargetId);
      if (opts?.reloadEvidence && profileId && skillId) setEvidence(await skillAPI.evidence(profileId, skillId));
      if (opts?.reloadRequirements && targetId && profileId)
        setRequirements(await skillAPI.requirements(profileId, targetId));
      setSuccess(message);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  const selectedTarget = targets.find(t => t.career_target_id === (targetId ?? selectedTargetId));
  const currentState = states.find(s => s.skill_id === skillId);
  const skillGaps = gaps?.gaps.filter(g => !skillId || g.skill_id === skillId) ?? [];

  // Stable top-level components are used below so input focus survives re-render.

  const sections = <nav aria-label="Skill intelligence sections" className="flex flex-wrap gap-2">
    {NAV.map(([title, href]) => <Link key={href} className={subBtn} href={href}>{title}</Link>)}
  </nav>;

  return <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
    <div className="mx-auto max-w-7xl space-y-6">
      <Link href="/" className="text-sm text-neutral-400 underline">Home</Link>
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">Skill Intelligence</h1>
        <p className="text-neutral-400">Your assessed skills, career targets, verified evidence, and suggested next actions.</p>
      </header>
      {sections}
      <section className={box}>
        <label className="block text-sm" htmlFor="profile-selector">Active profile</label>
        <select id="profile-selector" className={`${input} mt-2 max-w-lg`} value={profileId}
          onChange={e => { setProfileId(e.target.value); setSelectedTargetId(""); setError(""); }}>
          {!profileId && <option value="">No active profiles</option>}
          {profiles.filter(p => p.is_active).map(p => <option key={p.profile_id} value={p.profile_id}>
            {p.profile_name}{p.is_default ? " (default)" : ""}
          </option>)}
        </select>
      </section>
      {loading && <p role="status" className="text-neutral-400">Loading current backend data...</p>}
      {error && <p role="alert" className="rounded-xl border border-red-800 bg-red-950 p-3">{error}</p>}
      {success && <p role="status" className="rounded-xl border border-emerald-800 bg-emerald-950 p-3">{success}</p>}
      {!profileId && <section className={box}>
        <p>No active profile. Create one to begin.</p>
        <label htmlFor="new-profile" className="mt-3 block text-sm">Profile name</label>
        <input id="new-profile" className={input} value={newProfileName}
          onChange={e => setNewProfileName(e.target.value)} />
        <button className={`${btn} mt-3`} disabled={busy || !newProfileName.trim()}
          onClick={() => void mutate(async () => {
            await skillAPI.createProfile({profile_name: newProfileName.trim(), is_default: profiles.length === 0});
            await loadProfiles();
          }, "Profile created.")}>Create profile</button>
      </section>}

      {profileId && mode === "overview" && <div className="grid gap-4 md:grid-cols-2">
        <section className={box}><h2 className="text-xl font-semibold">Skill profile</h2>
          <p className="mt-3">{states.length} tracked skill states</p>
          <p className="text-sm text-neutral-400">Levels reflect your assessments, not AI inference.</p>
          <Link className="mt-4 inline-block underline" href="/skill-intelligence/profile">View skills</Link>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Career targets</h2>
          <p className="mt-3">{targets.length} recorded targets</p>
          <Link className="mt-4 inline-block underline" href="/skill-intelligence/career-targets">View career targets</Link>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Skill gaps</h2>
          {gaps ? <p className="mt-3">{gaps.summary.level_gaps} gaps; {gaps.summary.unknown_current_level} unknown current levels</p> : <p>No gap result.</p>}
          <ul className="mt-3 space-y-2">{(gaps?.gaps ?? []).slice(0, 5).map(g =>
            <li key={g.skill_id}><Link className="underline" href={`/skill-intelligence/skills/${encodeURIComponent(g.skill_id)}`}>{g.skill_name}</Link> — {g.gap_type}</li>)}</ul>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Next actions</h2>
          <p className="mt-3">{recommendations.length} recommendations; {queue.filter(q => q.status !== "completed" && q.status !== "removed").length} open queue items</p>
          <Link className="mt-4 inline-block underline" href="/skill-intelligence/recommendations">View recommendations</Link>
        </section>
      </div>}

      {profileId && mode === "profile" && <div className="space-y-4">
        <section className={box}><h2 className="mb-3 text-xl font-semibold">Track a skill</h2>
          <SkillSearch query={skillQuery} onQuery={setSkillQuery}
            options={skillOptions} selected={selectedSkillId} onSelected={setSelectedSkillId}
            busy={busy} onSearch={() => skillAPI.skills(skillQuery.trim()).then(setSkillOptions)
              .catch(e => setError(String(e)))} />
          <label className="mt-3 block text-sm">Current proficiency (human-assessed)</label>
          <LevelSelect levels={levels} value={levelId || null} onChange={v => setLevelId(v ?? "")} />
          <button className={`${btn} mt-3`} disabled={busy || !selectedSkillId}
            onClick={() => void mutate(() => skillAPI.saveState(profileId, selectedSkillId, {
              current_level_id: levelId || null, target_level_id: null, confidence: null,
              career_priority: 3, learning_status: "not_started", notes: null,
            }), "Skill state saved.")}>Track canonical skill</button>
          <p className="mt-2 text-sm text-neutral-400">Unknown is permitted; never infer a level from AI or a book mapping.</p>
        </section>
        {states.map(s => <SkillStateEditor key={`${profileId}:${s.skill_id}`} state={s} levels={levels}
          busy={busy} onSave={async (body) => mutate(() => skillAPI.saveState(profileId, s.skill_id, body), "Skill state updated.")} />)}
        {states.length === 0 && <section className={box}>No tracked skills. Search the canonical taxonomy above.</section>}
      </div>}

      {profileId && mode === "skill" && <div className="space-y-4">
        <section className={box}><h2 className="text-xl font-semibold">Skill: {skillId}</h2>
          <p className="mt-2">Current: {levels.find(l => l.level_id === currentState?.current_level_id)?.name ?? "Unknown"}</p>
          <p>Target: {levels.find(l => l.level_id === currentState?.target_level_id)?.name ?? "Unset"}</p>
          <p>Confidence: {num(currentState?.confidence)}</p>
          {skillGaps.map(g => <div className="mt-3 space-y-1" key={g.skill_id}>
            <span className={tag}>{g.gap_type}</span>
            <p>{g.explanation}</p>
            <p>Gap steps: {num(g.gap_steps)}</p>
            <p>Missing prerequisites: {g.missing_prerequisite_skill_ids.join(", ") || "None"}</p>
            <p>Approved supporting books: {g.approved_supporting_book_count}</p>
          </div>)}
          {!currentState && <p>No recorded skill state for this profile.</p>}
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Evidence and review</h2>
          <div className="mt-3 space-y-3">{evidence.map(e => <div key={e.evidence_id} className="rounded-xl border border-neutral-700 p-3">
            <p className="font-medium">{e.title}</p><span className={tag}>{e.verification_status}</span>
            <p className="text-sm text-neutral-400">{e.description}</p>
            {e.verification_status === "unverified" && <button className={`${subBtn} mt-2`} disabled={busy}
              onClick={() => void mutate(() => skillAPI.reviewEvidence(e.evidence_id, "reviewed"),
                "Evidence marked reviewed. Proficiency was not changed.", {reloadEvidence:true})}>Mark reviewed</button>}
          </div>)}{evidence.length === 0 && <p>No evidence linked to this skill.</p>}</div>
          <label htmlFor="evidence-title" className="mt-4 block text-sm">Evidence title</label>
          <input id="evidence-title" className={input} value={evidenceTitle} onChange={e => setEvidenceTitle(e.target.value)} />
          <label htmlFor="evidence-kind" className="mt-3 block text-sm">Evidence type</label>
          <select id="evidence-kind" className={input} value={evidenceType} onChange={e => setEvidenceType(e.target.value)}>
            {["manual","project","work_experience","certification","course","assessment","repository","exercise","publication"].map(t =>
              <option key={t} value={t}>{t}</option>)}
          </select>
          <button className={`${btn} mt-3`} disabled={busy || !currentState || !evidenceTitle.trim()}
            onClick={() => void mutate(() => skillAPI.addEvidence(profileId, skillId ?? "", {
              evidence_type:evidenceType, title:evidenceTitle.trim(),
            }), "Evidence added; current level unchanged.", {reloadEvidence:true})}>Add evidence</button>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Related recommendations</h2>
          {recommendations.filter(r => r.skill_id === skillId).map(r => <p key={r.recommendation_id} className="mt-2">{r.title}: {r.explanation}</p>)}
        </section>
      </div>}

      {profileId && mode === "targets" && <div className="space-y-4">
        <section className={box}><h2 className="text-xl font-semibold">Create career target</h2>
          <label htmlFor="role-name" className="mt-3 block text-sm">Role name</label>
          <input id="role-name" className={input} value={roleName} onChange={e => setRoleName(e.target.value)} />
          <label htmlFor="role-slug" className="mt-3 block text-sm">Unique role slug</label>
          <input id="role-slug" className={input} value={roleSlug} onChange={e => setRoleSlug(e.target.value)} />
          <label htmlFor="role-priority" className="mt-3 block text-sm">Priority (1–5)</label>
          <input id="role-priority" className={input} type="number" min={1} max={5} value={priority}
            onChange={e => setPriority(Number(e.target.value))} />
          <button className={`${btn} mt-3`} disabled={busy || !roleName.trim() || !roleSlug.trim() || priority < 1 || priority > 5}
            onClick={() => void mutate(() => skillAPI.createTarget({
              profile_id:profileId, role_name:roleName.trim(), role_slug:roleSlug.trim(),
              priority, status:"exploring",
            }), "Career target created.")}>Create target</button>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Career targets</h2>
          <div className="mt-3 space-y-3">{targets.map(t => <div key={t.career_target_id} className="rounded-xl border border-neutral-800 p-3">
            <Link className="font-medium underline" href={`/skill-intelligence/career-targets/${t.career_target_id}`}>{t.role_name}</Link>
            <p className="text-sm text-neutral-400">{t.status} · priority {t.priority}</p>
          </div>)}{targets.length === 0 && <p>No career targets.</p>}</div>
        </section>
      </div>}

      {profileId && mode === "target" && <div className="space-y-4">
        <section className={box}><h2 className="text-xl font-semibold">{selectedTarget?.role_name ?? "Career target"}</h2>
          <p>Status: {selectedTarget?.status ?? "Loading"}</p>
          <p>Requirements: {requirements.length}</p>
          <div className="mt-3 space-y-2">{requirements.map(r => <div className="rounded-xl border border-neutral-800 p-3" key={r.career_target_skill_id}>
            <p>{r.skill_id} · required level: {levels.find(l => l.level_id === r.required_level_id)?.name ?? r.required_level_id}</p>
            <p className="text-sm text-neutral-400">Importance: {r.importance_weight}; {r.is_required ? "required" : "optional"}</p>
          </div>)}</div>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Add or update required skill</h2>
          <SkillSearch query={skillQuery} onQuery={setSkillQuery}
            options={skillOptions} selected={selectedSkillId} onSelected={setSelectedSkillId}
            busy={busy} onSearch={() => skillAPI.skills(skillQuery.trim()).then(setSkillOptions)
              .catch(e => setError(String(e)))} />
          <label className="mt-3 block text-sm">Required canonical proficiency level</label>
          <LevelSelect levels={levels} value={levelId || null} onChange={v => setLevelId(v ?? "")} includeUnknown={false} />
          <button className={`${btn} mt-3`} disabled={busy || !selectedSkillId || !levelId}
            onClick={() => void mutate(() => skillAPI.saveRequirement(targetId ?? "", selectedSkillId, {
              required_level_id:levelId, importance_weight:3, is_required:true,
            }), "Requirement saved.", {reloadRequirements:true})}>Save requirement</button>
        </section>
        <section className={box}><h2 className="text-xl font-semibold">Deterministic role gaps</h2>
          {(gaps?.gaps ?? []).map(g => <div className="mt-3 rounded-xl border border-neutral-800 p-3" key={g.skill_id}>
            <Link className="underline" href={`/skill-intelligence/skills/${encodeURIComponent(g.skill_id)}`}>{g.skill_name}</Link>
            <p>{g.gap_type} · {g.gap_steps == null ? "unknown current" : `${g.gap_steps} level steps`}</p>
            <p className="text-sm text-neutral-400">{g.explanation}</p>
          </div>)}
          {gaps?.gaps.length === 0 && <p>No gaps for this target.</p>}
        </section>
      </div>}

      {profileId && mode === "recommendations" && <div className="space-y-4">
        <section className={box}>
          <h2 className="text-xl font-semibold">Recommendation inbox</h2>
          <label htmlFor="target-filter" className="mt-3 block text-sm">Career target (optional)</label>
          <select id="target-filter" className={input} value={selectedTargetId}
            onChange={e => setSelectedTargetId(e.target.value)}>
            <option value="">All profile recommendations</option>
            {targets.map(t => <option key={t.career_target_id} value={t.career_target_id}>{t.role_name}</option>)}
          </select>
          <button className={`${btn} mt-3`} disabled={busy} onClick={() => void mutate(() => skillAPI.generate(profileId, selectedTargetId || undefined),
            "Recommendation run generated from existing trusted inputs.")}>Generate recommendations</button>
        </section>
        {recommendations.map(r => <section key={r.recommendation_id} className={box}>
          <div className="flex flex-wrap items-center gap-2"><h3 className="text-lg font-semibold">{r.title}</h3>
            <span className={tag}>{r.recommendation_type}</span><span className={tag}>{r.decision_status}</span>
          </div>
          <p className="mt-2">{r.explanation}</p>
          <p className="mt-2 text-sm text-neutral-400">Priority score: {num(r.priority_score)} · Skill: {r.skill_id}</p>
          {r.recommended_document_id && <p className="text-sm">Trusted book: {r.recommended_document_id}</p>}
          <details className="mt-2"><summary className="cursor-pointer">Scoring explanation</summary>
            <pre className="overflow-x-auto whitespace-pre-wrap text-xs">{JSON.stringify(r.score_components, null, 2)}</pre>
            <p className="text-xs">Source mapping IDs: {r.source_mapping_ids.join(", ") || "None"}</p>
          </details>
          <div className="mt-3 flex flex-wrap gap-2">
            {r.decision_status === "new" && (["accepted", "deferred", "dismissed"] as const).map(st =>
              <button key={st} className={subBtn} disabled={busy} onClick={() => void mutate(() => skillAPI.decide(r.recommendation_id, st),
                `Recommendation ${st}.`)}>{st}</button>)}
            {r.decision_status === "accepted" && <button className={btn} disabled={busy}
              onClick={() => void mutate(() => skillAPI.enqueue(profileId, r.recommendation_id), "Added to reading queue.")}>Add to queue</button>}
          </div>
        </section>)}
        {recommendations.length === 0 && <section className={box}>No recommendation run results for this selection. Generate a run above.</section>}
      </div>}

      {profileId && mode === "queue" && <div className="space-y-4">
        <h2 className="text-xl font-semibold">Reading queue</h2>
        {queue.map(item => <QueueEditor key={item.reading_queue_item_id} item={item} busy={busy}
          onSave={body => mutate(() => skillAPI.updateQueue(item.reading_queue_item_id, body), "Queue progress updated.")} />)}
        {queue.length === 0 && <section className={box}>Queue empty. Accept a recommendation and add it from the inbox.</section>}
      </div>}
    </div>
  </main>;
}


// Define form controls outside the workspace component so React does not unmount
// inputs on each keystroke (and lose focus).
function LevelSelect({levels, value, onChange, includeUnknown=true}: {
  levels: ProficiencyLevel[];
  value: string | null;
  onChange: (v: string | null) => void;
  includeUnknown?: boolean;
}) {
  return <select aria-label="Canonical proficiency" className="w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2 text-neutral-100"
    value={value ?? ""} onChange={e => onChange(e.target.value || null)}>
    {includeUnknown && <option value="">Unknown / unset</option>}
    {levels.map(l => <option key={l.level_id} value={l.level_id}>{l.name} ({l.code})</option>)}
  </select>;
}

function SkillSearch({query, onQuery, options, selected, onSelected, busy, onSearch}: {
  query: string;
  onQuery: (value: string) => void;
  options: CanonicalSkill[];
  selected: string;
  onSelected: (value: string) => void;
  busy: boolean;
  onSearch: () => void;
}) {
  return <div className="space-y-2">
    <label htmlFor="skill-query" className="block text-sm">Find canonical skill</label>
    <div className="flex flex-wrap gap-2">
      <input id="skill-query" className="w-full flex-1 rounded-lg border border-neutral-700 bg-neutral-950 p-2 text-neutral-100"
        value={query} onChange={e => onQuery(e.target.value)} placeholder="Search skill name or alias" />
      <button type="button" className="rounded-lg border border-neutral-700 px-3 py-2"
        disabled={busy || !query.trim()} onClick={onSearch}>Search</button>
    </div>
    <select aria-label="Canonical skill" className="w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2 text-neutral-100"
      value={selected} onChange={e => onSelected(e.target.value)}>
      <option value="">Select a canonical skill</option>
      {options.map(sk => <option key={sk.skill_id} value={sk.skill_id}>{sk.name}</option>)}
    </select>
  </div>;
}

// Keep form draft state local and isolated per skill; this prevents edits from leaking
// from one tracked skill to another when switching profiles.
function SkillStateEditor({state, levels, busy, onSave}: {
  state: SkillState; levels: ProficiencyLevel[]; busy: boolean;
  onSave: (body: Partial<SkillState>) => Promise<void>;
}) {
  const [current, setCurrent] = useState(state.current_level_id ?? "");
  const [target, setTarget] = useState(state.target_level_id ?? "");
  const [confidence, setConfidence] = useState(state.confidence == null ? "" : String(state.confidence));
  const [priority, setPriority] = useState(state.career_priority);
  const [status, setStatus] = useState(state.learning_status);
  useEffect(() => {
    setCurrent(state.current_level_id ?? ""); setTarget(state.target_level_id ?? "");
    setConfidence(state.confidence == null ? "" : String(state.confidence));
    setPriority(state.career_priority); setStatus(state.learning_status);
  }, [state]);
  const validConfidence = confidence === "" || (Number.isFinite(Number(confidence)) && Number(confidence) >= 0 && Number(confidence) <= 1);
  return <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
    <Link className="font-medium underline" href={`/skill-intelligence/skills/${encodeURIComponent(state.skill_id)}`}>{state.skill_id}</Link>
    <div className="mt-3 grid gap-3 md:grid-cols-3">
      <label className="text-sm">Current level
        <select className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" value={current} onChange={e => setCurrent(e.target.value)}>
          <option value="">Unknown</option>{levels.map(l => <option key={l.level_id} value={l.level_id}>{l.name}</option>)}
        </select>
      </label>
      <label className="text-sm">Target level
        <select className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" value={target} onChange={e => setTarget(e.target.value)}>
          <option value="">Unset</option>{levels.map(l => <option key={l.level_id} value={l.level_id}>{l.name}</option>)}
        </select>
      </label>
      <label className="text-sm">Confidence (0–1; blank unknown)
        <input className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" type="number" step="0.05" min="0" max="1"
          value={confidence} onChange={e => setConfidence(e.target.value)} />
      </label>
      <label className="text-sm">Career priority (1–5)
        <input className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" type="number" min="1" max="5"
          value={priority} onChange={e => setPriority(Number(e.target.value))} />
      </label>
      <label className="text-sm">Learning status
        <select className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" value={status} onChange={e => setStatus(e.target.value)}>
          {["not_started", "planned", "learning", "practicing", "demonstrated", "maintained", "paused"].map(st => <option key={st}>{st}</option>)}
        </select>
      </label>
    </div>
    <button className="mt-4 rounded-lg bg-white px-3 py-2 text-neutral-950 disabled:opacity-40"
      disabled={busy || !validConfidence || priority < 1 || priority > 5}
      onClick={() => void onSave({
        current_level_id: current || null, target_level_id: target || null,
        confidence: confidence ? Number(confidence) : null,
        career_priority: priority, learning_status: status, notes: state.notes,
      })}>Save skill assessment</button>
  </section>;
}

function QueueEditor({item, busy, onSave}: {
  item: QueueItem; busy: boolean;
  onSave: (body: {status?: QueueItem["status"]; progress_percent?: number; notes?: string;
    priority?: number; planned_start?: string | null; target_finish?: string | null}) => Promise<void>;
}) {
  const [progress, setProgress] = useState(item.progress_percent);
  const [notes, setNotes] = useState(item.notes ?? "");
  const [start, setStart] = useState(item.planned_start ?? "");
  const [finish, setFinish] = useState(item.target_finish ?? "");
  useEffect(() => { setProgress(item.progress_percent); setNotes(item.notes ?? "");
    setStart(item.planned_start ?? ""); setFinish(item.target_finish ?? ""); }, [item]);
  return <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
    <p className="font-medium">{item.document_id ? `Book ${item.document_id}` : `Skill ${item.skill_id ?? "action"}`}</p>
    <p className="text-sm text-neutral-400">{item.status}; priority {item.priority}</p>
    <div className="mt-3 grid gap-3 md:grid-cols-3">
      <label className="text-sm">Progress (manual %)
        <input className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" type="number" min="0" max="100"
          value={progress} onChange={e => setProgress(Number(e.target.value))} />
      </label>
      <label className="text-sm">Start date
        <input type="date" className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" value={start} onChange={e => setStart(e.target.value)} />
      </label>
      <label className="text-sm">Target finish
        <input type="date" className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" value={finish} onChange={e => setFinish(e.target.value)} />
      </label>
    </div>
    <label className="mt-3 block text-sm">Notes
      <textarea className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" value={notes} onChange={e => setNotes(e.target.value)} />
    </label>
    <div className="mt-3 flex flex-wrap gap-2">
      <button className="rounded-lg bg-white px-3 py-2 text-neutral-950 disabled:opacity-40"
        disabled={busy || progress < 0 || progress > 100 || !!(start && finish && finish < start)}
        onClick={() => void onSave({
          progress_percent:progress, notes, planned_start:start || null, target_finish:finish || null,
        })}>Save progress</button>
      {item.status === "queued" && <button className="rounded-lg border border-neutral-700 px-3 py-2"
        disabled={busy} onClick={() => void onSave({status:"active"})}>Start</button>}
      {item.status === "active" && <button className="rounded-lg border border-neutral-700 px-3 py-2"
        disabled={busy} onClick={() => void onSave({status:"paused"})}>Pause</button>}
      {(item.status === "active" || item.status === "paused") && <button className="rounded-lg border border-neutral-700 px-3 py-2"
        disabled={busy} onClick={() => void onSave({status:"completed", progress_percent:100})}>Mark completed</button>}
    </div>
  </section>;
}