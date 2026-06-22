type SourceLike = {
  source_number?: number;
  score: number;
  document_id?: string | null;
  filename: string | null;
  title: string | null;
  author?: string | null;
  file_type?: string | null;
  primary_domain?: string | null;
  domains: string[] | null;
  page_number: number | null;
  page_start: number | null;
  page_end: number | null;
  page_numbers?: number[] | null;
  chunk_index: number | null;
  chunk_preview?: string | null;
  text?: string | null;
  chunk_text?: string | null;
};

type SourceCardProps = {
  source: SourceLike;
  rank?: number;
};

function formatPages(source: SourceLike): string {
  if (source.page_start !== null && source.page_end !== null) {
    if (source.page_start === source.page_end) {
      return String(source.page_start);
    }

    return `${source.page_start}-${source.page_end}`;
  }

  if (source.page_number !== null) {
    return String(source.page_number);
  }

  return "N/A";
}

function getPreview(source: SourceLike): string {
  return (
    source.chunk_preview ||
    source.chunk_text ||
    source.text ||
    "No chunk preview available."
  );
}

export function SourceCard({ source, rank }: SourceCardProps) {
  const label =
    rank !== undefined
      ? `Rank ${rank}`
      : source.source_number
      ? `Source ${source.source_number}`
      : "Source";

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
      <div className="flex flex-wrap gap-2 text-xs text-neutral-500">
        <span>{label}</span>
        <span>•</span>
        <span>Score: {source.score.toFixed(4)}</span>
        <span>•</span>
        <span>Pages: {formatPages(source)}</span>
        <span>•</span>
        <span>Chunk: {source.chunk_index ?? "N/A"}</span>
      </div>

      <h3 className="mt-2 font-medium text-neutral-100">
        {source.title || "Unknown title"}
      </h3>

      <p className="mt-1 text-sm text-neutral-500">
        {source.filename || "Unknown file"}
      </p>

      {source.primary_domain && (
        <p className="mt-2 text-xs text-neutral-500">
          Primary domain: {source.primary_domain}
        </p>
      )}

      <p className="mt-1 text-xs text-neutral-500">
        Domains: {(source.domains || []).join(", ") || "N/A"}
      </p>

      <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-neutral-300">
        {getPreview(source)}
      </p>
    </div>
  );
}