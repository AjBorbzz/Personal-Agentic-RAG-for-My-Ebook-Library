import Link from "next/link";
import type { ViewData } from "./skill-view-data";

const box = "workspace-panel";

export function SkillOverview({
  states = [],
  targets = [],
  gaps,
  recommendations = [],
  queue = [],
}: ViewData) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <section className={box}>
        <h2 className="text-xl font-semibold">Skill profile</h2>
        <p className="mt-3">{states.length} tracked skill states</p>
        <p className="text-sm text-neutral-400">
          Levels reflect your assessments, not AI inference.
        </p>
        <Link
          className="mt-4 inline-block underline"
          href="/skill-intelligence/profile"
        >
          View skills
        </Link>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Career targets</h2>
        <p className="mt-3">{targets.length} recorded targets</p>
        <Link
          className="mt-4 inline-block underline"
          href="/skill-intelligence/career-targets"
        >
          View career targets
        </Link>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Skill gaps</h2>
        {gaps ? (
          <p className="mt-3">
            {gaps.summary.level_gaps} gaps; {gaps.summary.unknown_current_level}{" "}
            unknown current levels
          </p>
        ) : (
          <p>No gap result.</p>
        )}
        <ul className="mt-3 space-y-2">
          {(gaps?.gaps ?? []).slice(0, 5).map((g) => (
            <li key={g.skill_id}>
              <Link
                className="underline"
                href={`/skill-intelligence/skills/${encodeURIComponent(
                  g.skill_id,
                )}`}
              >
                {g.skill_name}
              </Link>{" "}
              — {g.gap_type}
            </li>
          ))}
        </ul>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Next actions</h2>
        <p className="mt-3">
          {recommendations.length} recommendations;{" "}
          {
            queue.filter(
              (q) => q.status !== "completed" && q.status !== "removed",
            ).length
          }{" "}
          open queue items
        </p>
        <Link
          className="mt-4 inline-block underline"
          href="/skill-intelligence/recommendations"
        >
          View recommendations
        </Link>
      </section>
    </div>
  );
}
