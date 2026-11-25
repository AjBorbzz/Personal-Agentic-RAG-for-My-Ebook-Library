"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { WorkspaceIcon } from "./WorkspaceIcon";
import { workspaceGroups } from "./workspace-navigation";

export function WorkspaceHeader() {
  const pathname = usePathname();

  return (
    <header className="workspace-header">
      <a className="workspace-skip" href="#main-content">
        Skip to content
      </a>
      <div className="workspace-header-inner">
        <Link
          href="/"
          className="workspace-brand"
          aria-current={pathname === "/" ? "page" : undefined}
        >
          <span className="workspace-mark">
            <WorkspaceIcon name="book" />
          </span>
          <span>
            <strong>Personal Agentic RAG</strong>
            <span>For my ebooks</span>
          </span>
        </Link>
        <nav aria-label="Workspace" className="workspace-nav">
          {workspaceGroups.map(({ label, tools }) => {
            const [{ href }] = tools;
            const isCurrent = tools.some(
              (tool) =>
                pathname === tool.href || pathname.startsWith(`${tool.href}/`),
            );

            return (
              <Link
                key={href}
                href={href}
                aria-current={
                  pathname === href
                    ? "page"
                    : isCurrent
                      ? "location"
                      : undefined
                }
              >
                {label}
              </Link>
            );
          })}
        </nav>
        <Link
          href="/health"
          className="workspace-health"
          aria-current={pathname === "/health" ? "page" : undefined}
        >
          <WorkspaceIcon name="pulse" />
          <span>Backend health</span>
        </Link>
      </div>
    </header>
  );
}
