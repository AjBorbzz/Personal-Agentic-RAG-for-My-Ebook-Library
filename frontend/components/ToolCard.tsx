import Link from "next/link";

type ToolCardProps = {
  title: string;
  description: string;
  href: string;
  status?: "ready" | "debug" | "planned";
};

export function ToolCard({
  title,
  description,
  href,
  status = "ready",
}: ToolCardProps) {
  const statusLabel = {
    ready: "Ready",
    debug: "Debug",
    planned: "Planned",
  }[status];

  return (
    <Link
      href={href}
      className="group rounded-2xl border border-neutral-800 bg-neutral-900 p-5 transition hover:border-neutral-600 hover:bg-neutral-850"
    >
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-lg font-semibold text-white group-hover:text-neutral-100">
          {title}
        </h2>

        <span className="rounded-full border border-neutral-700 px-2 py-1 text-xs text-neutral-400">
          {statusLabel}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-neutral-400">{description}</p>

      <p className="mt-5 text-sm font-medium text-neutral-300 group-hover:text-white">
        Open →
      </p>
    </Link>
  );
}