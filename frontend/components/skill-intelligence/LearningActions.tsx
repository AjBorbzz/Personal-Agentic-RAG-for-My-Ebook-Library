"use client";

import Link from "next/link";
import { skillAPI } from "@/lib/skill-intelligence-api";
import type { ViewData } from "./skill-view-data";
import type { ViewAction } from "./skill-view-data";
import { QueueEditor } from "./SkillEditors";

type Interactive = { profileId: string; busy: boolean; mutate: ViewAction };
const box = "workspace-panel";
const input = "workspace-field";
const btn = "workspace-button";
const subBtn = "workspace-button workspace-button--secondary";
const tag = "workspace-badge";
const num = (value: number | string | null | undefined) =>
  value == null ? "Unknown" : String(value);

type RecommendationProps = Interactive & {
  data: ViewData;
  selectedTargetId: string;
  changeTarget: (id: string) => void;
  recommendationsLoaded: boolean;
};

export function Recommendations({
  data,
  profileId,
  busy,
  mutate,
  selectedTargetId,
  changeTarget,
  recommendationsLoaded,
}: RecommendationProps) {
  const { targets = [], recommendations = [] } = data;
  return (
    <div className="space-y-4">
      <section className={box}>
        <h2 className="text-xl font-semibold">Recommendation inbox</h2>
        <label htmlFor="target-filter" className="mt-3 block text-sm">
          Career target (optional)
        </label>
        <select
          id="target-filter"
          className={input}
          value={selectedTargetId}
          disabled={busy}
          onChange={(e) => changeTarget(e.target.value)}
        >
          <option value="">All profile recommendations</option>
          {targets.map((t) => (
            <option key={t.career_target_id} value={t.career_target_id}>
              {t.role_name}
            </option>
          ))}
        </select>
        <button
          className={`${btn} mt-3`}
          disabled={busy}
          onClick={() =>
            void mutate(
              () => skillAPI.generate(profileId, selectedTargetId || undefined),
              "Recommendation run generated from existing trusted inputs.",
            )
          }
        >
          Generate recommendations
        </button>
      </section>
      {recommendationsLoaded &&
        recommendations.map((r) => (
          <section key={r.recommendation_id} className={box}>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold">{r.title}</h3>
              <span className={tag}>{r.recommendation_type}</span>
              <span className={tag}>{r.decision_status}</span>
            </div>
            <p className="mt-2">{r.explanation}</p>
            <p className="mt-2 text-sm text-neutral-400">
              Priority score: {num(r.priority_score)} · Skill:{" "}
              <Link
                className="break-all underline"
                href={`/skill-intelligence/skills/${encodeURIComponent(
                  r.skill_id,
                )}`}
              >
                {r.skill_id}
              </Link>
            </p>
            {r.recommended_document_id && (
              <p className="text-sm">
                Trusted book:{" "}
                <Link
                  className="break-all underline"
                  href={`/documents/${encodeURIComponent(
                    r.recommended_document_id,
                  )}/metadata`}
                >
                  {r.recommended_document_id}
                </Link>
              </p>
            )}
            <details className="mt-2">
              <summary className="cursor-pointer">Scoring explanation</summary>
              <pre className="overflow-x-auto whitespace-pre-wrap text-xs">
                {JSON.stringify(r.score_components, null, 2)}
              </pre>
              <p className="text-xs wrap-anywhere">
                Source mapping IDs: {r.source_mapping_ids.join(", ") || "None"}
              </p>
            </details>
            <div className="mt-3 flex flex-wrap gap-2">
              {r.decision_status === "new" &&
                (["accepted", "deferred", "dismissed"] as const).map((st) => (
                  <button
                    key={st}
                    className={subBtn}
                    disabled={busy}
                    onClick={() =>
                      void mutate(
                        () => skillAPI.decide(r.recommendation_id, st),
                        `Recommendation ${st}.`,
                      )
                    }
                  >
                    {st}
                  </button>
                ))}
              {r.decision_status === "accepted" && (
                <button
                  className={btn}
                  disabled={busy}
                  onClick={() =>
                    void mutate(
                      () => skillAPI.enqueue(profileId, r.recommendation_id),
                      "Added to reading queue.",
                    )
                  }
                >
                  Add to queue
                </button>
              )}
            </div>
          </section>
        ))}
      {recommendationsLoaded && recommendations.length === 0 && (
        <section className={box}>
          No recommendation run results for this selection. Generate a run
          above.
        </section>
      )}
    </div>
  );
}

export function ReadingQueue({
  data,
  busy,
  mutate,
}: Omit<Interactive, "profileId"> & { data: ViewData }) {
  const { queue = [] } = data;
  return (
    <div className="space-y-4">
      {queue.map((item) => (
        <QueueEditor
          key={JSON.stringify([
            item.reading_queue_item_id,
            item.progress_percent,
            item.planned_start,
            item.target_finish,
            item.notes,
          ])}
          item={item}
          busy={busy}
          onSave={(body) =>
            mutate(
              () => skillAPI.updateQueue(item.reading_queue_item_id, body),
              "Queue progress updated.",
            )
          }
        />
      ))}
      {queue.length === 0 && (
        <section className={box}>
          Queue empty. Accept a recommendation and add it from the inbox.
        </section>
      )}
    </div>
  );
}
