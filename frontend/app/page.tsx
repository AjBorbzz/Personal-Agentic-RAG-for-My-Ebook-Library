import Link from "next/link";

const tools = [
  {
    title: "RAG Chat",
    description: "Ask questions against your indexed ebook library.",
    href: "/rag-chat",
  },
  {
    title: "Agentic RAG",
    description: "Ask with intent routing, domain detection, and fallback retrieval.",
    href: "/agentic-rag",
  },
  {
    title: "Learning Path",
    description: "Generate source-backed learning plans.",
    href: "/learning-path",
  },
  {
    title: "Project Generator",
    description: "Generate portfolio-grade project plans.",
    href: "/project-generator",
  },
  {
    title: "Architecture Review",
    description: "Review system designs for risks, gaps, and improvements.",
    href: "/architecture-review",
  },
  {
    title: "Code Review",
    description: "Review pasted code using your ebook-backed knowledge base.",
    href: "/code-review",
  },
  {
  title: "Backend Health",
  description: "Check if the frontend can connect to FastAPI.",
  href: "/health",
},
];

export default function Home() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100">
      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="mb-10">
          <p className="mb-2 text-sm uppercase tracking-wide text-neutral-400">
            Personal Agentic RAG
          </p>
          <h1 className="text-4xl font-bold tracking-tight">
            Local AI Knowledge Dashboard
          </h1>
          <p className="mt-4 max-w-3xl text-neutral-300">
            A private dashboard for ebook RAG, agentic retrieval, learning paths,
            project generation, architecture review, and code review.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tools.map((tool) => (
            <Link
              key={tool.href}
              href={tool.href}
              className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 transition hover:border-neutral-600 hover:bg-neutral-850"
            >
              <h2 className="text-xl font-semibold">{tool.title}</h2>
              <p className="mt-2 text-sm leading-6 text-neutral-400">
                {tool.description}
              </p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}