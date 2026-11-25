const paths = {
  book: (
    <>
      <path d="M12 5.5C9 3.4 5.5 3.2 3 4.5v14c2.5-1.3 6-1.1 9 1 3-2.1 6.5-2.3 9-1v-14c-2.5-1.3-6-1.1-9 1Z" />
      <path d="M12 5.5v14M6 8.5a7 7 0 0 1 3 .5m6 0a7 7 0 0 1 3-.5" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 4 4M8 10.5h5" />
    </>
  ),
  learning: (
    <>
      <path d="M3 19h18M5 15l5-5 4 3 6-7m-5 0h5v5" />
      <circle cx="5" cy="15" r="1" />
    </>
  ),
  build: (
    <>
      <rect x="4" y="7" width="16" height="13" rx="2" />
      <path d="M9 7V4h6v3M4 12h16m-9 0v2h2v-2" />
    </>
  ),
  pulse: <path d="M3 12h4l3-6 4 12 3-6h4" />,
  chevron: <path d="m9 6 6 6-6 6" />,
};

export type WorkspaceIconName = keyof typeof paths;

export function WorkspaceIcon({
  name,
  className,
}: {
  name: WorkspaceIconName;
  className?: string;
}) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {paths[name]}
    </svg>
  );
}
