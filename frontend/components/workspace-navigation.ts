import type { WorkspaceIconName } from "./WorkspaceIcon";

type WorkspaceGroup = {
  label: string;
  icon: WorkspaceIconName;
  tools: { title: string; href: string }[];
};

export const workspaceGroups: WorkspaceGroup[] = [
  {
    label: "Library",
    icon: "book",
    tools: [
      { title: "Document Library", href: "/documents" },
      { title: "Ingest and Index", href: "/ingest" },
      { title: "Ingestion Jobs", href: "/ingestion-jobs" },
      { title: "Book Curator", href: "/book-curator" },
    ],
  },
  {
    label: "Retrieval",
    icon: "search",
    tools: [
      { title: "Semantic Search", href: "/search" },
      { title: "RAG Chat", href: "/rag-chat" },
      { title: "Agentic RAG", href: "/agentic-rag" },
      { title: "RAG Evaluation", href: "/evaluation" },
    ],
  },
  {
    label: "Learning",
    icon: "learning",
    tools: [
      { title: "Skill Intelligence", href: "/skill-intelligence" },
      { title: "Learning Path", href: "/learning-path" },
      { title: "Skill Taxonomy", href: "/skill-taxonomy" },
      { title: "Book-to-Skill Dashboard", href: "/book-skill-dashboard" },
    ],
  },
  {
    label: "Portfolio",
    icon: "build",
    tools: [
      { title: "Portfolio Builder", href: "/portfolio-builder" },
      { title: "Project Generator", href: "/project-generator" },
      { title: "Architecture Review", href: "/architecture-review" },
      { title: "Code Review", href: "/code-review" },
    ],
  },
];
