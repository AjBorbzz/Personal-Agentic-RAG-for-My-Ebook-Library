"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
};

export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="space-y-4 leading-7 text-neutral-200">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mt-6 text-3xl font-bold text-white">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-6 text-2xl font-semibold text-white">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-5 text-xl font-semibold text-white">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="text-neutral-200">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="ml-6 list-disc space-y-2">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="ml-6 list-decimal space-y-2">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-neutral-200">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-white">{children}</strong>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-neutral-700 pl-4 text-neutral-400">
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const isBlock = className?.includes("language-");

            if (isBlock) {
              return (
                <code className="block overflow-x-auto rounded-lg bg-neutral-950 p-4 text-sm text-neutral-100">
                  {children}
                </code>
              );
            }

            return (
              <code className="rounded bg-neutral-800 px-1.5 py-0.5 text-sm text-neutral-100">
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="overflow-x-auto rounded-xl border border-neutral-800 bg-neutral-950 p-4">
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-neutral-800 text-sm">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-neutral-800 bg-neutral-900 px-3 py-2 text-left font-semibold text-white">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-neutral-800 px-3 py-2 text-neutral-200">
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}