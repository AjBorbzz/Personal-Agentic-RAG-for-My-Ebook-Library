import { ToolCard } from "@/components/ToolCard";

const tools = [
  {
    title: "Ingest and Index",
    description: "Upload PDFs, EPUBs, or TXT files and index them into Qdrant.",
    href: "/ingest",
  },
  {
    title: "Semantic Search",
    description: "Inspect retrieved chunks directly before LLM generation.",
    href: "/search",
  },
  {
    title: "RAG Chat",
    description: "Ask questions against your indexed ebook library.",
    href: "/rag-chat",
  },
  {
    title: "Agentic RAG",
    description:
      "Use intent classification, domain-aware routing, query rewriting, and fallback retrieval.",
    href: "/agentic-rag",
  },
  {
    title: "Learning Path",
    description: "Generate structured study plans from your ebook knowledge base.",
    href: "/learning-path",
  },
  {
    title: "Project Generator",
    description:
      "Generate portfolio-grade project plans with architecture, APIs, database design, and resume bullets.",
    href: "/project-generator",
  },
  {
    title: "Architecture Review",
    description:
      "Review system designs for security, scalability, reliability, data modeling, and deployment.",
    href: "/architecture-review",
  },
  {
    title: "Code Review",
    description:
      "Paste code and review it for correctness, security, reliability, maintainability, and testing.",
    href: "/code-review",
  },
  {
    title: "Backend Health",
    description: "Verify that the FastAPI backend is reachable.",
    href: "/health",
  },
  {
  title: "Document Library",
  description:
    "View registered documents, versions, active status, and deprecated sources.",
  href: "/documents",
},
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-7xl">
        <div className="mb-10">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-neutral-500">
            Personal Agentic RAG
          </p>

          <h1 className="mt-4 max-w-4xl text-4xl font-bold tracking-tight text-white md:text-5xl">
            Ebook-powered AI learning and portfolio assistant
          </h1>

          <p className="mt-5 max-w-3xl text-lg leading-8 text-neutral-400">
            A local AI system for ingesting technical ebooks, searching indexed
            knowledge, generating source-backed answers, building learning
            paths, creating project plans, reviewing architectures, and
            reviewing code.
          </p>
        </div>

        <div className="mb-8 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Backend
            </p>
            <p className="mt-2 text-lg font-semibold text-white">FastAPI</p>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Vector DB
            </p>
            <p className="mt-2 text-lg font-semibold text-white">Qdrant</p>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Local LLM
            </p>
            <p className="mt-2 text-lg font-semibold text-white">Ollama</p>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              Frontend
            </p>
            <p className="mt-2 text-lg font-semibold text-white">Next.js</p>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {tools.map((tool) => (
            <ToolCard
              key={tool.href}
              title={tool.title}
              description={tool.description}
              href={tool.href}
            />
          ))}
        </div>
      </section>
    </main>
  );
}