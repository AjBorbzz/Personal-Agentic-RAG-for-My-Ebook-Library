"use client";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { useEffect, useState } from "react";

import {
  fetchSkillDetail,
  fetchSkillTree,
  searchSkills,
} from "@/lib/skill-taxonomy-api";

import type {
  SkillCategoryTree,
  SkillDetail,
  SkillListItem,
  SkillTaxonomyTree,
} from "@/lib/skill-taxonomy-types";

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function SkillButton({
  skill,
  selected,
  onSelect,
}: {
  skill: SkillListItem;
  selected: boolean;
  onSelect: (skillId: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(skill.skill_id)}
      className={
        "w-full rounded-xl border p-3 text-left " +
        "transition " +
        (selected
          ? "border-neutral-500 bg-neutral-800"
          : "border-neutral-800 bg-neutral-950/60 hover:bg-neutral-800/60")
      }
    >
      <p className="font-medium text-white">{skill.name}</p>

      <div className="mt-2 flex flex-wrap gap-2">
        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
          {formatLabel(skill.skill_type)}
        </span>

        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
          {formatLabel(skill.difficulty_level)}
        </span>
      </div>
    </button>
  );
}

function CategoryNode({
  category,
  selectedSkillId,
  onSelectSkill,
}: {
  category: SkillCategoryTree;
  selectedSkillId: string | null;
  onSelectSkill: (skillId: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <h4 className="font-medium text-neutral-200">{category.name}</h4>

        {category.description ? (
          <p className="mt-1 text-sm leading-6 text-neutral-500">
            {category.description}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        {category.skills.map((skill) => (
          <SkillButton
            key={skill.skill_id}
            skill={skill}
            selected={selectedSkillId === skill.skill_id}
            onSelect={onSelectSkill}
          />
        ))}
      </div>

      {category.children.length ? (
        <div className="ml-4 space-y-4 border-l border-neutral-800 pl-4">
          {category.children.map((child) => (
            <CategoryNode
              key={child.category_id}
              category={child}
              selectedSkillId={selectedSkillId}
              onSelectSkill={onSelectSkill}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function SkillTaxonomyPage() {
  const [tree, setTree] = useState<SkillTaxonomyTree | null>(null);

  const [searchQuery, setSearchQuery] = useState("");

  const [searchResults, setSearchResults] = useState<SkillListItem[]>([]);

  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null);

  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null);

  const [loading, setLoading] = useState(true);
  const [loadingSkill, setLoadingSkill] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [skillError, setSkillError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [skillRevision, setSkillRevision] = useState(0);
  const [searchComplete, setSearchComplete] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    fetchSkillTree({ signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) setTree(result);
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load taxonomy.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedSkillId) return;

    const controller = new AbortController();

    fetchSkillDetail(selectedSkillId, { signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) setSelectedSkill(result);
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setSkillError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load skill.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingSkill(false);
      });

    return () => controller.abort();
  }, [selectedSkillId, skillRevision]);

  function selectSkill(skillId: string) {
    if (skillId === selectedSkillId && !skillError) return;

    setSelectedSkillId(skillId);
    setSkillRevision((current) => current + 1);
    setSelectedSkill(null);
    setSkillError(null);
    setLoadingSkill(true);
  }

  async function runSearch() {
    if (searching) return;

    setSearching(true);
    setSearchComplete(false);
    setSearchError(null);

    try {
      const result = await searchSkills(searchQuery);

      setSearchResults(result.results);
      setSearchComplete(true);
    } catch (requestError) {
      setSearchError(
        requestError instanceof Error
          ? requestError.message
          : "Skill search failed.",
      );
    } finally {
      setSearching(false);
    }
  }

  return (
    <PageFrame width="wide" className="space-y-6">
      <PageHeader
        title="Skill Taxonomy"
        description="Browse canonical skills, their aliases, and the prerequisites that connect technical domains."
      />

      {error && <StatusMessage tone="error">{error}</StatusMessage>}

      {tree ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Domains
            </p>
            <p className="mt-3 text-3xl font-semibold text-white">
              {tree.domain_count}
            </p>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Categories
            </p>
            <p className="mt-3 text-3xl font-semibold text-white">
              {tree.category_count}
            </p>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Skills
            </p>
            <p className="mt-3 text-3xl font-semibold text-white">
              {tree.skill_count}
            </p>
          </div>
        </div>
      ) : null}

      <section className="workspace-panel min-w-0">
        <h2 className="text-xl font-semibold text-white">Search skills</h2>

        <form
          className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            void runSearch();
          }}
        >
          <div className="min-w-0 flex-1">
            <Field label="Skill name or alias">
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="RAG, XSOAR, Python, FastAPI"
                className="workspace-field"
              />
            </Field>
          </div>
          <button
            type="submit"
            disabled={searching}
            className="workspace-button"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        {searching && (
          <StatusMessage tone="info">Searching skills…</StatusMessage>
        )}
        {searchError && (
          <StatusMessage tone="error">{searchError}</StatusMessage>
        )}
        {searchComplete && searchResults.length === 0 && (
          <StatusMessage tone="info">
            No skills match your search.
          </StatusMessage>
        )}

        {searchResults.length ? (
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {searchResults.map((skill) => (
              <SkillButton
                key={skill.skill_id}
                skill={skill}
                selected={selectedSkillId === skill.skill_id}
                onSelect={selectSkill}
              />
            ))}
          </div>
        ) : null}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="workspace-panel min-w-0">
          <h2 className="text-xl font-semibold text-white">
            Taxonomy explorer
          </h2>

          {loading ? (
            <p className="mt-6 text-neutral-400">Loading taxonomy…</p>
          ) : (
            <div className="mt-6 space-y-8">
              {tree?.domains.map((domain) => (
                <div key={domain.domain_id} className="space-y-5">
                  <div>
                    <h3 className="text-2xl font-semibold text-white">
                      {domain.name}
                    </h3>

                    {domain.description ? (
                      <p className="mt-2 text-sm leading-6 text-neutral-400">
                        {domain.description}
                      </p>
                    ) : null}
                  </div>

                  {domain.uncategorized_skills.length ? (
                    <div className="grid gap-2 md:grid-cols-2">
                      {domain.uncategorized_skills.map((skill) => (
                        <SkillButton
                          key={skill.skill_id}
                          skill={skill}
                          selected={selectedSkillId === skill.skill_id}
                          onSelect={selectSkill}
                        />
                      ))}
                    </div>
                  ) : null}

                  <div className="space-y-6">
                    {domain.categories.map((category) => (
                      <CategoryNode
                        key={category.category_id}
                        category={category}
                        selectedSkillId={selectedSkillId}
                        onSelectSkill={selectSkill}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <aside className="workspace-panel h-fit min-w-0 xl:sticky xl:top-6">
          <h2 className="text-xl font-semibold text-white">Skill details</h2>

          {skillError && (
            <StatusMessage tone="error">{skillError}</StatusMessage>
          )}
          {loadingSkill && (
            <StatusMessage tone="info">Loading skill details…</StatusMessage>
          )}
          {!loadingSkill &&
            !skillError &&
            (!selectedSkill ? (
              <p className="mt-4 text-sm leading-6 text-neutral-500">
                Select a skill to inspect its aliases, prerequisites, related
                skills, and metadata.
              </p>
            ) : (
              <div className="mt-5 space-y-6">
                <div>
                  <h3 className="text-2xl font-semibold text-white">
                    {selectedSkill.skill.name}
                  </h3>

                  <p className="mt-1 text-sm text-neutral-500">
                    {selectedSkill.skill.domain_name}
                    {selectedSkill.skill.category_name
                      ? ` · ${selectedSkill.skill.category_name}`
                      : ""}
                  </p>

                  {selectedSkill.skill.description ? (
                    <p className="mt-4 text-sm leading-6 text-neutral-300">
                      {selectedSkill.skill.description}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300">
                    {formatLabel(selectedSkill.skill.skill_type)}
                  </span>

                  <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300">
                    {formatLabel(selectedSkill.skill.difficulty_level)}
                  </span>
                </div>

                <div>
                  <h4 className="font-medium text-white">Aliases</h4>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedSkill.aliases.map((alias) => (
                      <span
                        key={alias.alias_id}
                        className="rounded-full bg-neutral-800 px-3 py-1 text-xs text-neutral-300"
                      >
                        {alias.alias}
                      </span>
                    ))}

                    {!selectedSkill.aliases.length ? (
                      <span className="text-sm text-neutral-500">
                        No aliases
                      </span>
                    ) : null}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-white">
                    Prerequisites and outgoing relationships
                  </h4>

                  <div className="mt-3 space-y-3">
                    {selectedSkill.outgoing_relationships.map(
                      (relationship) => (
                        <div
                          key={relationship.relationship_id}
                          className="rounded-xl border border-neutral-800 bg-neutral-950 p-3"
                        >
                          <p className="text-sm font-medium text-neutral-200">
                            {relationship.target_skill_name}
                          </p>

                          <p className="mt-1 text-xs text-neutral-500">
                            {formatLabel(relationship.relationship_type)}
                            {" · "}
                            {Math.round(relationship.strength * 100)}%
                          </p>
                        </div>
                      ),
                    )}

                    {!selectedSkill.outgoing_relationships.length ? (
                      <p className="text-sm text-neutral-500">
                        No outgoing relationships
                      </p>
                    ) : null}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-white">Used by</h4>

                  <div className="mt-3 space-y-3">
                    {selectedSkill.incoming_relationships.map(
                      (relationship) => (
                        <div
                          key={relationship.relationship_id}
                          className="rounded-xl border border-neutral-800 bg-neutral-950 p-3"
                        >
                          <p className="text-sm font-medium text-neutral-200">
                            {relationship.source_skill_name}
                          </p>

                          <p className="mt-1 text-xs text-neutral-500">
                            {formatLabel(relationship.relationship_type)}
                          </p>
                        </div>
                      ),
                    )}

                    {!selectedSkill.incoming_relationships.length ? (
                      <p className="text-sm text-neutral-500">
                        No incoming relationships
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
        </aside>
      </div>
    </PageFrame>
  );
}
