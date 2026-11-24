"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  portfolioApi, type Profile, type Target, type Opportunity, type Project,
  type Milestone, type Artifact, type Readiness,
} from "../../lib/portfolio-api";

type View = "dashboard" | "opportunities" | "new" | "project" | "architecture" | "artifacts" | "readiness";
const panel = "rounded-2xl border border-neutral-800 bg-neutral-900 p-5";
const field = "w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2 text-neutral-100 focus:outline-none focus:ring-2 focus:ring-neutral-500";
const action = "rounded-lg bg-white px-3 py-2 text-sm font-semibold text-neutral-950 disabled:opacity-50";
const secondary = "rounded-lg border border-neutral-600 px-3 py-2 text-sm text-neutral-100";

export default function PortfolioWorkspace({ view, id }: { view: View; id?: string }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [profileId, setProfileId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [problem, setProblem] = useState("");
  const [skill, setSkill] = useState("");
  const [specJson, setSpecJson] = useState("");
  const [notes, setNotes] = useState("Reviewed specification against the stated scope and source links.");
  const [milestoneTitle, setMilestoneTitle] = useState("");
  const [criteria, setCriteria] = useState("");
  const [artifactTitle, setArtifactTitle] = useState("");
  const [artifactContent, setArtifactContent] = useState("");
  const [artifactType, setArtifactType] = useState("repository");
  const [reviewId, setReviewId] = useState("");
  const [reviewScope, setReviewScope] = useState("implemented");
  const [reviewStatus, setReviewStatus] = useState("reviewed");
  const [evidenceJson, setEvidenceJson] = useState('{"repository_ref":""}');
  const [reviewUrl, setReviewUrl] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");

  const refresh = useCallback(async () => {
    if (id) {
      const [p, m, a, r] = await Promise.all([
        portfolioApi.project(id), portfolioApi.milestones(id),
        portfolioApi.artifacts(id), portfolioApi.readiness(id),
      ]);
      setProject(p); setMilestones(m); setArtifacts(a); setReadiness(r);
    } else if (profileId) {
      const found = await portfolioApi.projects(profileId, targetId || undefined);
      setProjects(found);
      if (targetId) setOpportunities(await portfolioApi.opportunities(profileId, targetId));
    }
  }, [id, profileId, targetId]);

  useEffect(() => {
    portfolioApi.profiles().then(rows => {
      setProfiles(rows);
      const active = rows.find(p => p.is_active);
      if (active) setProfileId(active.profile_id);
    }).catch(e => setError(String(e)));
  }, []);
  useEffect(() => {
    if (!profileId) return;
    portfolioApi.targets(profileId).then(rows => {
      setTargets(rows);
      const selected = rows.find(x => x.status === "active");
      setTargetId(selected?.career_target_id ?? "");
    }).catch(e => setError(String(e)));
  }, [profileId]);
  useEffect(() => { refresh().catch(e => setError(String(e))); }, [refresh]);

  async function run(task: () => Promise<unknown>, success: string) {
    setBusy(true); setError(""); setNotice("");
    try { await task(); setNotice(success); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  const projectUrl = project ? `/portfolio-builder/projects/${project.portfolio_project_id}` : "#";

  return <main className="mx-auto max-w-6xl space-y-5 p-6 text-neutral-100">
    <header className={panel}>
      <h1 className="text-2xl font-semibold">Portfolio Builder</h1>
      <p className="mt-1 text-sm text-neutral-400">Phase 15. Project plans remain plans until human-reviewed implementation evidence is recorded.</p>
      <nav className="mt-4 flex flex-wrap gap-3 text-sm underline">
        <Link href="/portfolio-builder">Dashboard</Link>
        <Link href="/portfolio-builder/opportunities">Opportunities</Link>
        <Link href="/portfolio-builder/projects/new">New project</Link>
        <Link href="/portfolio-builder/publication-readiness">Readiness</Link>
      </nav>
    </header>
    {error && <div role="alert" className="rounded-lg border border-red-800 p-3 text-red-200">{error}</div>}
    {notice && <div role="status" className="rounded-lg border border-neutral-600 p-3">{notice}</div>}
    {!id && <section className={panel}>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">Active profile
          <select aria-label="Profile" className={field} value={profileId} onChange={e => setProfileId(e.target.value)}>
            <option value="">Select a profile</option>
            {profiles.map(x => <option key={x.profile_id} value={x.profile_id}>{x.profile_name}</option>)}
          </select>
        </label>
        <label className="block text-sm">Career target (must be active)
          <select aria-label="Career target" className={field} value={targetId} onChange={e => setTargetId(e.target.value)}>
            <option value="">Select active target</option>
            {targets.filter(x => x.status === "active").map(x => <option key={x.career_target_id} value={x.career_target_id}>{x.role_name}</option>)}
          </select>
        </label>
      </div>
    </section>}
    {(view === "dashboard" || view === "opportunities") && <section className={panel}>
      <h2 className="text-lg font-semibold">Actionable skill gaps and trusted sources</h2>
      {!targetId && <p className="text-neutral-400">Select an active career target to list opportunities.</p>}
      <div className="mt-4 space-y-3">
        {opportunities.map(x => <div key={x.skill_id} className="rounded-xl border border-neutral-800 p-3">
          <p className="font-semibold">{x.skill_name} — {x.gap_type}</p>
          <p className="text-sm text-neutral-400">{x.explanation}</p>
          <p className="text-xs">Trusted books: {x.source_document_ids.length} {x.no_trusted_book_sources && "— no approved sources available"}</p>
          <button className={secondary} onClick={() => {
            setSkill(x.skill_id); setTitle(x.title_suggestion);
            setSlug(x.skill_name.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"") + "-portfolio");
            setProblem(`Demonstrate ${x.skill_name} with a testable, evidence-backed application.`);
            window.location.hash = "create";
          }}>Use for new project</button>
        </div>)}
      </div>
    </section>}
    {!id && (view === "new" || view === "opportunities" || view === "dashboard") && <section id="create" className={panel}>
      <h2 className="text-lg font-semibold">Create a project idea — 15A/15B</h2>
      <div className="mt-3 space-y-3">
        <label className="block">Gap skill ID <select className={field} value={skill} onChange={e => setSkill(e.target.value)}><option value="">Select gap</option>
          {opportunities.map(x => <option key={x.skill_id} value={x.skill_id}>{x.skill_name}</option>)}
        </select></label>
        <label className="block">Project title <input className={field} value={title} onChange={e=>setTitle(e.target.value)}/></label>
        <label className="block">Slug <input className={field} value={slug} onChange={e=>setSlug(e.target.value)}/></label>
        <label className="block">Problem statement <textarea className={field} rows={3} value={problem} onChange={e=>setProblem(e.target.value)}/></label>
        <button disabled={busy || !profileId || !targetId || !skill} className={action} onClick={() => run(async () => {
          const made = await portfolioApi.create({profile_id:profileId, career_target_id:targetId, title, slug, problem_statement:problem, target_skill_ids:[skill]});
          window.location.assign(`/portfolio-builder/projects/${made.portfolio_project_id}`);
        }, "Project created")}>Create idea</button>
      </div>
    </section>}
    {!id && <section className={panel}>
      <h2 className="text-lg font-semibold">Existing projects</h2>
      {projects.length === 0 ? <p className="text-neutral-400">No projects found for selected profile/target.</p> :
        <ul className="mt-3 space-y-2">{projects.map(p => <li key={p.portfolio_project_id}>
          <Link className="underline" href={`/portfolio-builder/projects/${p.portfolio_project_id}`}>{p.title}</Link> <span className="text-sm text-neutral-400">({p.status})</span>
        </li>)}</ul>}
    </section>}
    {project && <section className={panel}>
      <h2 className="text-xl font-semibold">{project.title}</h2>
      <p className="text-sm text-neutral-400">Status: {project.status}; approved blueprint: {project.approved_blueprint_version ?? "none"}</p>
      <p className="mt-2">{project.problem_statement}</p>
      <p className="mt-2 text-sm">Canonical target skills: {project.target_skill_ids.join(", ")} | Approved mapping IDs: {project.source_mapping_ids.length}</p>
      <div className="mt-3 flex flex-wrap gap-3 text-sm underline">
        <Link href={projectUrl}>Workspace</Link>
        <Link href={`${projectUrl}/architecture`}>Architecture</Link>
        <Link href={`${projectUrl}/artifacts`}>Artifacts</Link>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {(["planned", "in_progress", "blocked", "completed", "published", "archived"] as const).map(s =>
          <button key={s} className={secondary} disabled={busy || project.status === s} onClick={()=>run(()=>portfolioApi.status(project.portfolio_project_id,s),`Project status: ${s}`)}>{s}</button>)}
      </div>
    </section>}
    {project && (view === "project" || view === "architecture") && <section className={panel}>
      <h2 className="text-lg font-semibold">Blueprints — 15C</h2>
      <p className="text-sm text-neutral-400">Run the existing Project Generator Agent using this project's approved gap skills and constraints. Review its output, then paste the exact JSON. This phase does not duplicate its prompt or Ollama client.</p>
      <textarea aria-label="Project Generator JSON" className={`${field} mt-3 font-mono text-xs`} rows={7} value={specJson} onChange={e=>setSpecJson(e.target.value)} placeholder="Paste complete /project-generator response JSON"/>
      <button className={action} disabled={busy} onClick={()=>run(async()=>{
        const parsed: unknown = JSON.parse(specJson);
        if(!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Expected a JSON object");
        await portfolioApi.blueprint(project.portfolio_project_id, parsed as Record<string,unknown>);
      }, "Blueprint version saved for human review")}>Save blueprint version</button>
      <div className="mt-3 space-y-2">{project.blueprint_versions.map(v => <div key={v.version} className="rounded-lg border border-neutral-800 p-2">
        <span>Version {v.version} — {v.approved ? "approved" : "unapproved"}</span>
        <button className={`${secondary} ml-3`} disabled={busy || v.approved} onClick={()=>run(()=>portfolioApi.approve(project.portfolio_project_id,v.version,notes),"Human-approved version saved")}>Approve reviewed version</button>
      </div>)}</div>
      <label className="mt-3 block">Review notes <textarea className={field} rows={2} value={notes} onChange={e=>setNotes(e.target.value)}/></label>
      {view === "architecture" && <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-lg bg-neutral-950 p-3 text-sm">{JSON.stringify(project.architecture,null,2)}</pre>}
    </section>}
    {project && view === "project" && <section className={panel}>
      <h2 className="text-lg font-semibold">Milestones — 15D</h2>
      <div className="mt-3 flex flex-col gap-2">
        <input className={field} placeholder="Milestone title" value={milestoneTitle} onChange={e=>setMilestoneTitle(e.target.value)}/>
        <input className={field} placeholder="One acceptance criterion" value={criteria} onChange={e=>setCriteria(e.target.value)}/>
        <button className={action} disabled={busy} onClick={()=>run(()=>portfolioApi.addMilestone(project.portfolio_project_id,{title:milestoneTitle,description:"",sequence_order:milestones.length+1,acceptance_criteria:[criteria]}),"Milestone added")}>Add milestone</button>
      </div>
      <ul className="mt-4 space-y-3">{milestones.map(m => <li key={m.milestone_id} className="rounded-lg border border-neutral-800 p-3">
        <p className="font-medium">{m.sequence_order}. {m.title} — {m.status}</p>
        <p className="text-xs text-neutral-400">{m.acceptance_criteria.join("; ")}</p>
        <button className={`${secondary} mt-2`} onClick={()=>{
          const text=window.prompt("Human acceptance notes (required to complete milestone)",m.completion_notes||"");
          if (text!==null) run(()=>portfolioApi.milestoneStatus(m.milestone_id,"completed",text),"Milestone completion recorded");
        }}>Mark completed with notes</button>
      </li>)}</ul>
    </section>}
    {project && (view === "artifacts" || view === "project") && <section className={panel}>
      <h2 className="text-lg font-semibold">Artifacts and human review — 15D–15F</h2>
      <div className="mt-3 flex flex-wrap gap-2">{(["README", "architecture", "case_study", "resume_bullet", "interview_story"] as const).map(kind =>
        <button key={kind} className={secondary} disabled={busy} onClick={()=>run(()=>portfolioApi.draft(project.portfolio_project_id,kind),"Draft created; claim scope remains planned")}>Draft {kind}</button>)}</div>
      <div className="mt-4 space-y-2">
        <label className="block">Artifact type <select className={field} value={artifactType} onChange={e=>setArtifactType(e.target.value)}>
          {(["repository","architecture","README","test_report","demo","case_study","resume_bullet","interview_story","publication"] as const).map(x=><option key={x} value={x}>{x}</option>)}
        </select></label>
        <input className={field} placeholder="Artifact title" value={artifactTitle} onChange={e=>setArtifactTitle(e.target.value)}/>
        <textarea className={field} placeholder="Artifact content or summary" value={artifactContent} rows={3} onChange={e=>setArtifactContent(e.target.value)}/>
        <button className={action} disabled={busy} onClick={()=>run(()=>portfolioApi.addArtifact(project.portfolio_project_id,{artifact_type:artifactType,title:artifactTitle,content:artifactContent}),"Draft artifact saved")}>Add draft artifact</button>
      </div>
      <div className="mt-4 space-y-2">{artifacts.map(a=><div key={a.artifact_id} className="rounded-lg border border-neutral-800 p-3 text-sm">
        <p className="font-medium">{a.title} — {a.claim_scope} / {a.verification_status} (v{a.version})</p>
        <p className="max-h-24 overflow-auto whitespace-pre-wrap text-neutral-400">{a.content}</p>
        <button className={`${secondary} mt-2`} onClick={()=>{setReviewId(a.artifact_id);setReviewScope(a.claim_scope);setReviewStatus(a.verification_status)}}>Review evidence</button>
      </div>)}</div>
      {reviewId && <div className="mt-5 space-y-2 rounded-lg border border-neutral-700 p-3">
        <p className="font-semibold">Review artifact {reviewId}</p>
        <label className="block">Claim scope <select className={field} value={reviewScope} onChange={e=>setReviewScope(e.target.value)}>
          {(["planned","implemented","tested","measured","published"] as const).map(x=><option key={x}>{x}</option>)}
        </select></label>
        <label className="block">Verification status <select className={field} value={reviewStatus} onChange={e=>setReviewStatus(e.target.value)}>
          {(["draft","reviewed","verified","published"] as const).map(x=><option key={x}>{x}</option>)}
        </select></label>
        <label className="block">Evidence JSON <textarea className={`${field} font-mono text-xs`} rows={5} value={evidenceJson} onChange={e=>setEvidenceJson(e.target.value)}/></label>
        <label className="block">Publication URL (only when published) <input className={field} value={reviewUrl} onChange={e=>setReviewUrl(e.target.value)}/></label>
        <label className="block">Review notes <input className={field} value={reviewNotes} onChange={e=>setReviewNotes(e.target.value)}/></label>
        <button className={action} disabled={busy} onClick={()=>run(()=>portfolioApi.reviewArtifact(reviewId,{
          claim_scope:reviewScope, verification_status:reviewStatus, evidence:JSON.parse(evidenceJson),
          source_url: reviewUrl || null, review_notes:reviewNotes,
        }),"Evidence review saved; version incremented")}>Save human review</button>
      </div>}
    </section>}
    {project && (view === "project" || view === "readiness") && <section className={panel}>
      <h2 className="text-lg font-semibold">Publication readiness — 15G</h2>
      {readiness && <><p>Ready: {String(readiness.publication_ready)}</p><p>Milestones: {readiness.completed_milestones}/{readiness.milestone_count}; verified artifacts: {readiness.verified_artifact_count}</p>
        <ul className="mt-2 list-inside list-disc text-sm text-neutral-300">{readiness.missing.map(x=><li key={x}>{x}</li>)}</ul></>}
      <button className={`${secondary} mt-3`} disabled={busy} onClick={()=>run(async()=>{const proposals=await portfolioApi.evidenceProposals(project.portfolio_project_id);setNotice(`Human review proposals: ${JSON.stringify(proposals)}`)},"Evidence proposals loaded")}>View personal-skill evidence proposals (read-only)</button>
    </section>}
    {view === "readiness" && !id && <section className={panel}><h2>Publication readiness</h2>
      <p className="text-sm text-neutral-400">Select a project above, then open its workspace and review the readiness panel.</p>
    </section>}
  </main>;
}