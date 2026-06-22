type MetadataCardProps = {
  label: string;
  value: string | number | null | undefined;
  mono?: boolean;
};

export function MetadataCard({ label, value, mono = false }: MetadataCardProps) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
      <p className="text-xs uppercase tracking-wide text-neutral-500">
        {label}
      </p>

      <p
        className={`mt-2 text-sm text-neutral-200 ${
          mono ? "break-all font-mono" : ""
        }`}
      >
        {value ?? "N/A"}
      </p>
    </div>
  );
}