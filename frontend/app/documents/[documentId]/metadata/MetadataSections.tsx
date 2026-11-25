import { useState } from "react";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import type {
  DocumentRecord,
  EnrichedBookMetadata,
  QdrantSyncResponse,
} from "./metadata-types";

const textFields = [
  { key: "title", label: "Title" },
  { key: "author", label: "Author" },
  { key: "subtitle", label: "Subtitle" },
  { key: "publisher", label: "Publisher" },
  { key: "edition", label: "Edition" },
  { key: "language", label: "Language" },
  { key: "isbn_10", label: "ISBN-10" },
  { key: "isbn_13", label: "ISBN-13" },
] as const;

const listFields = [
  {
    key: "topics",
    label: "Topics",
    placeholder: "authentication, API design, distributed systems",
  },
  {
    key: "technologies",
    label: "Technologies",
    placeholder: "Python, FastAPI, PostgreSQL",
  },
  {
    key: "tags",
    label: "Tags",
    placeholder: "backend, system design, security",
  },
  {
    key: "prerequisite_skills",
    label: "Prerequisite skills",
    placeholder: "Python fundamentals, databases",
  },
] as const;

const difficultyLevels = [
  "Unknown",
  "Beginner",
  "Intermediate",
  "Advanced",
  "Mixed",
];

function dateLabel(value: string | null) {
  if (!value) return null;

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function ExistingValue({
  label,
  value,
  wide = false,
}: {
  label: string;
  value: string | number | string[] | null;
  wide?: boolean;
}) {
  const displayValue = Array.isArray(value) ? value.join(", ") : value;

  return (
    <div
      className={`min-w-0 rounded-lg border border-neutral-800 bg-neutral-950 p-3 ${
        wide ? "sm:col-span-2" : ""
      }`}
    >
      <dt className="text-xs uppercase tracking-wide text-neutral-400">
        {label}
      </dt>
      <dd className="mt-1 whitespace-pre-wrap text-sm text-neutral-300 [overflow-wrap:anywhere]">
        {displayValue == null || displayValue === "" ? "N/A" : displayValue}
      </dd>
    </div>
  );
}

export function ReviewStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "border-yellow-800 bg-yellow-950 text-yellow-300",
    approved: "border-green-800 bg-green-950 text-green-300",
    rejected: "border-red-800 bg-red-950 text-red-300",
  };

  return (
    <span className={`workspace-badge capitalize ${styles[status] ?? ""}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function TrustedMetadata({ document }: { document: DocumentRecord }) {
  return (
    <section className="workspace-panel min-w-0">
      <h2 className="text-xl font-semibold">Trusted metadata</h2>
      <p className="mt-2 text-sm text-neutral-400">
        Current values stored in PostgreSQL.
      </p>
      <dl className="mt-5 grid min-w-0 gap-3 sm:grid-cols-2">
        {textFields.map(({ key, label }) => (
          <ExistingValue key={key} label={label} value={document[key]} />
        ))}
        <ExistingValue
          label="Publication year"
          value={document.publication_year}
        />
        <ExistingValue label="Difficulty" value={document.difficulty_level} />
        {listFields.map(({ key, label }) => (
          <ExistingValue key={key} label={label} value={document[key]} />
        ))}
        <ExistingValue label="Description" value={document.description} wide />
        <ExistingValue
          label="Metadata source"
          value={document.metadata_source}
        />
        <ExistingValue
          label="Confidence"
          value={document.metadata_confidence}
        />
        <ExistingValue
          label="Enriched"
          value={dateLabel(document.enriched_at)}
        />
        <ExistingValue
          label="Reviewed"
          value={dateLabel(document.metadata_reviewed_at)}
        />
      </dl>
    </section>
  );
}

function ListField({
  label,
  placeholder,
  values,
  onChange,
}: {
  label: string;
  placeholder: string;
  values: string[];
  onChange: (value: string[]) => void;
}) {
  const [draft, setDraft] = useState(values.join(", "));

  return (
    <Field label={label} hint="Separate values with commas.">
      <textarea
        rows={3}
        value={draft}
        placeholder={placeholder}
        className="workspace-field"
        onChange={(event) => {
          const text = event.target.value;
          setDraft(text);
          onChange(
            text
              .split(",")
              .map((value) => value.trim())
              .filter(Boolean),
          );
        }}
      />
    </Field>
  );
}

export function CandidateMetadata({
  candidate,
  edited,
  onChange,
}: {
  candidate: EnrichedBookMetadata | null;
  edited: boolean;
  onChange: <K extends keyof EnrichedBookMetadata>(
    field: K,
    value: EnrichedBookMetadata[K],
  ) => void;
}) {
  return (
    <section className="workspace-panel min-w-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Candidate metadata</h2>
          <p className="mt-2 text-sm text-neutral-400">
            Review and edit before approval.
          </p>
        </div>
        {edited && <span className="workspace-badge">Edited</span>}
      </div>

      <div className="mt-5">
        {candidate ? (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              {textFields.map(({ key, label }) => (
                <Field key={key} label={label}>
                  <input
                    value={candidate[key] ?? ""}
                    onChange={(event) =>
                      onChange(key, event.target.value || null)
                    }
                    className="workspace-field"
                  />
                </Field>
              ))}
              <Field label="Publication year">
                <input
                  type="number"
                  min={1000}
                  max={2100}
                  value={candidate.publication_year ?? ""}
                  onChange={(event) =>
                    onChange(
                      "publication_year",
                      event.target.value ? Number(event.target.value) : null,
                    )
                  }
                  className="workspace-field"
                />
              </Field>
              <Field label="Difficulty">
                <select
                  value={candidate.difficulty_level ?? "unknown"}
                  onChange={(event) =>
                    onChange("difficulty_level", event.target.value)
                  }
                  className="workspace-field"
                >
                  {difficultyLevels.map((level) => (
                    <option key={level} value={level.toLowerCase()}>
                      {level}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            <Field label="Description">
              <textarea
                rows={5}
                value={candidate.description ?? ""}
                onChange={(event) =>
                  onChange("description", event.target.value || null)
                }
                className="workspace-field"
              />
            </Field>

            {listFields.map(({ key, label, placeholder }) => (
              <ListField
                key={key}
                label={label}
                placeholder={placeholder}
                values={candidate[key]}
                onChange={(values) => onChange(key, values)}
              />
            ))}

            <Field
              label={`Confidence (${candidate.metadata_confidence.toFixed(2)})`}
            >
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={candidate.metadata_confidence}
                onChange={(event) =>
                  onChange("metadata_confidence", Number(event.target.value))
                }
                className="w-full"
              />
            </Field>
          </div>
        ) : (
          <StatusMessage tone="info">
            No candidate has been generated yet.
          </StatusMessage>
        )}
      </div>
    </section>
  );
}

export function QdrantStatus({
  busy,
  syncing,
  result,
  onSync,
}: {
  busy: boolean;
  syncing: boolean;
  result: QdrantSyncResponse | null;
  onSync: () => void;
}) {
  return (
    <section className="workspace-panel min-w-0">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Qdrant synchronization</h2>
          <p className="mt-2 text-sm text-neutral-400">
            Copy approved metadata to every indexed chunk.
          </p>
        </div>
        <button
          type="button"
          onClick={onSync}
          disabled={busy}
          className="workspace-button workspace-button--secondary"
        >
          {syncing ? "Synchronizing…" : "Synchronize Qdrant"}
        </button>
      </div>
      {result && (
        <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <ExistingValue label="Collection" value={result.collection_name} />
          <ExistingValue label="Matched chunks" value={result.matched_points} />
          <ExistingValue
            label="Payload keys set"
            value={result.payload_keys_set}
          />
          <ExistingValue
            label="Indexes created"
            value={result.created_indexes}
          />
        </dl>
      )}
    </section>
  );
}
