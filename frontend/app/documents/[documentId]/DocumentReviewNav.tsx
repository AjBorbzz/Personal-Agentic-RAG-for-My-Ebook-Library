import { SectionNav } from "@/components/WorkspaceUI";

export function DocumentReviewNav({ documentId }: { documentId: string }) {
  const path = `/documents/${encodeURIComponent(documentId)}`;

  return (
    <div className="mt-4">
      <SectionNav
        label="Document review"
        items={[
          { label: "Metadata", href: `${path}/metadata` },
          { label: "Book evaluation", href: `${path}/curation` },
          { label: "Skill mappings", href: `${path}/skills` },
        ]}
      />
    </div>
  );
}
