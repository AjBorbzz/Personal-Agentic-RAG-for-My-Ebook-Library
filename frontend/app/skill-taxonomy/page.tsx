"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useState,
} from "react";

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
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
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
      onClick={() =>
        onSelect(skill.skill_id)
      }
      className={
        "w-full rounded-xl border p-3 text-left " +
        "transition " +
        (selected
          ? "border-neutral-500 bg-neutral-800"
          : "border-neutral-800 bg-neutral-950/60 hover:bg-neutral-800/60")
      }
    >
      <p className="font-medium text-white">
        {skill.name}
      </p>

      <div className="mt-2 flex flex-wrap gap-2">
        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
          {formatLabel(skill.skill_type)}
        </span>

        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
          {formatLabel(
            skill.difficulty_level
          )}
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
  onSelectSkill: (
    skillId: string
  ) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <h4 className="font-medium text-neutral-200">
          {category.name}
        </h4>

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
            selected={
              selectedSkillId
              === skill.skill_id
            }
            onSelect={onSelectSkill}
          />
        ))}
      </div>

      {category.children.length ? (
        <div className="ml-4 space-y-4 border-l border-neutral-800 pl-4">
          {category.children.map(
            (child) => (
              <CategoryNode
                key={child.category_id}
                category={child}
                selectedSkillId={
                  selectedSkillId
                }
                onSelectSkill={
                  onSelectSkill
                }
              />
            ),
          )}
        </div>
      ) : null}
    </div>
  );
}


export default function SkillTaxonomyPage() {
  const [tree, setTree] =
    useState<SkillTaxonomyTree | null>(
      null,
    );

  const [searchQuery, setSearchQuery] =
    useState("");

  const [searchResults, setSearchResults] =
    useState<SkillListItem[]>([]);

  const [selectedSkillId, setSelectedSkillId] =
    useState<string | null>(null);

  const [selectedSkill, setSelectedSkill] =
    useState<SkillDetail | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [searching, setSearching] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);


  const loadTree = useCallback(
    async () => {
      setLoading(true);
      setError(null);

      try {
        const result =
          await fetchSkillTree();

        setTree(result);
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load taxonomy.",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );


  useEffect(() => {
    void loadTree();
  }, [loadTree]);


  async function selectSkill(
    skillId: string,
  ) {
    setSelectedSkillId(skillId);
    setError(null);

    try {
      const result =
        await fetchSkillDetail(
          skillId
        );

      setSelectedSkill(result);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load skill.",
      );
    }
  }


  async function runSearch() {
    setSearching(true);
    setError(null);

    try {
      const result =
        await searchSkills(
          searchQuery
        );

      setSearchResults(
        result.results
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Skill search failed.",
      );
    } finally {
      setSearching(false);
    }
  }


  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-7xl space-y-8">
        <header>
          <Link
            href="/"
            className="text-sm font-medium text-blue-400 hover:text-blue-300 hover:underline"
          >
            ← Back to tools
          </Link>

          <p className="mt-8 text-sm font-medium uppercase tracking-[0.3em] text-neutral-500">
            Knowledge Structure
          </p>

          <h1 className="mt-4 text-4xl font-bold tracking-tight text-white md:text-5xl">
            Skill Taxonomy
          </h1>

          <p className="mt-5 max-w-3xl text-lg leading-8 text-neutral-400">
            Explore canonical technical skills,
            domains, categories, prerequisites,
            aliases, and related competencies.
          </p>
        </header>

        {error ? (
          <div className="rounded-2xl border border-red-900/70 bg-red-950/50 p-5 text-red-200">
            {error}
          </div>
        ) : null}

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

        <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
          <h2 className="text-xl font-semibold text-white">
            Search skills
          </h2>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <input
              value={searchQuery}
              onChange={(event) =>
                setSearchQuery(
                  event.target.value
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter"
                ) {
                  void runSearch();
                }
              }}
              placeholder="Search RAG, XSOAR, Python, FastAPI…"
              className="flex-1 rounded-xl border border-neutral-700 bg-neutral-950 px-4 py-2.5 text-neutral-100 outline-none focus:border-neutral-500"
            />

            <button
              type="button"
              disabled={searching}
              onClick={() =>
                void runSearch()
              }
              className="rounded-xl bg-white px-5 py-2.5 font-medium text-neutral-950 hover:bg-neutral-200 disabled:opacity-50"
            >
              {searching
                ? "Searching…"
                : "Search"}
            </button>
          </div>

          {searchResults.length ? (
            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {searchResults.map(
                (skill) => (
                  <SkillButton
                    key={skill.skill_id}
                    skill={skill}
                    selected={
                      selectedSkillId
                      === skill.skill_id
                    }
                    onSelect={selectSkill}
                  />
                ),
              )}
            </div>
          ) : null}
        </section>

        <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-semibold text-white">
              Taxonomy explorer
            </h2>

            {loading ? (
              <p className="mt-6 text-neutral-400">
                Loading taxonomy…
              </p>
            ) : (
              <div className="mt-6 space-y-8">
                {tree?.domains.map(
                  (domain) => (
                    <div
                      key={domain.domain_id}
                      className="space-y-5"
                    >
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

                      {domain
                        .uncategorized_skills
                        .length ? (
                        <div className="grid gap-2 md:grid-cols-2">
                          {domain
                            .uncategorized_skills
                            .map((skill) => (
                              <SkillButton
                                key={
                                  skill.skill_id
                                }
                                skill={skill}
                                selected={
                                  selectedSkillId
                                  === skill.skill_id
                                }
                                onSelect={
                                  selectSkill
                                }
                              />
                            ))}
                        </div>
                      ) : null}

                      <div className="space-y-6">
                        {domain.categories.map(
                          (category) => (
                            <CategoryNode
                              key={
                                category.category_id
                              }
                              category={
                                category
                              }
                              selectedSkillId={
                                selectedSkillId
                              }
                              onSelectSkill={
                                selectSkill
                              }
                            />
                          ),
                        )}
                      </div>
                    </div>
                  ),
                )}
              </div>
            )}
          </section>

          <aside className="h-fit rounded-2xl border border-neutral-800 bg-neutral-900 p-6 xl:sticky xl:top-6">
            <h2 className="text-xl font-semibold text-white">
              Skill details
            </h2>

            {!selectedSkill ? (
              <p className="mt-4 text-sm leading-6 text-neutral-500">
                Select a skill to inspect its
                aliases, prerequisites, related
                skills, and metadata.
              </p>
            ) : (
              <div className="mt-5 space-y-6">
                <div>
                  <h3 className="text-2xl font-semibold text-white">
                    {
                      selectedSkill.skill
                        .name
                    }
                  </h3>

                  <p className="mt-1 text-sm text-neutral-500">
                    {
                      selectedSkill.skill
                        .domain_name
                    }
                    {selectedSkill.skill
                      .category_name
                      ? ` · ${selectedSkill.skill.category_name}`
                      : ""}
                  </p>

                  {selectedSkill.skill
                    .description ? (
                    <p className="mt-4 text-sm leading-6 text-neutral-300">
                      {
                        selectedSkill.skill
                          .description
                      }
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300">
                    {formatLabel(
                      selectedSkill.skill
                        .skill_type
                    )}
                  </span>

                  <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300">
                    {formatLabel(
                      selectedSkill.skill
                        .difficulty_level
                    )}
                  </span>
                </div>

                <div>
                  <h4 className="font-medium text-white">
                    Aliases
                  </h4>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedSkill.aliases.map(
                      (alias) => (
                        <span
                          key={alias.alias_id}
                          className="rounded-full bg-neutral-800 px-3 py-1 text-xs text-neutral-300"
                        >
                          {alias.alias}
                        </span>
                      ),
                    )}

                    {!selectedSkill.aliases
                      .length ? (
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
                    {selectedSkill
                      .outgoing_relationships
                      .map((relationship) => (
                        <div
                          key={
                            relationship
                              .relationship_id
                          }
                          className="rounded-xl border border-neutral-800 bg-neutral-950 p-3"
                        >
                          <p className="text-sm font-medium text-neutral-200">
                            {
                              relationship
                                .target_skill_name
                            }
                          </p>

                          <p className="mt-1 text-xs text-neutral-500">
                            {formatLabel(
                              relationship
                                .relationship_type
                            )}
                            {" · "}
                            {Math.round(
                              relationship
                                .strength *
                                100,
                            )}
                            %
                          </p>
                        </div>
                      ))}

                    {!selectedSkill
                      .outgoing_relationships
                      .length ? (
                      <p className="text-sm text-neutral-500">
                        No outgoing relationships
                      </p>
                    ) : null}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-white">
                    Used by
                  </h4>

                  <div className="mt-3 space-y-3">
                    {selectedSkill
                      .incoming_relationships
                      .map((relationship) => (
                        <div
                          key={
                            relationship
                              .relationship_id
                          }
                          className="rounded-xl border border-neutral-800 bg-neutral-950 p-3"
                        >
                          <p className="text-sm font-medium text-neutral-200">
                            {
                              relationship
                                .source_skill_name
                            }
                          </p>

                          <p className="mt-1 text-xs text-neutral-500">
                            {formatLabel(
                              relationship
                                .relationship_type
                            )}
                          </p>
                        </div>
                      ))}

                    {!selectedSkill
                      .incoming_relationships
                      .length ? (
                      <p className="text-sm text-neutral-500">
                        No incoming relationships
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
}