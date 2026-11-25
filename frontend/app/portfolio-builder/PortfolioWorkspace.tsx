"use client";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { SectionNav } from "@/components/WorkspaceUI";
import { PortfolioBrowse } from "./PortfolioBrowse";
import { PortfolioProject } from "./PortfolioProject";

export type BrowseView = "dashboard" | "opportunities" | "new" | "readiness";
export type ProjectView = "project" | "architecture" | "artifacts";
type WorkspaceProps = { view: BrowseView } | { view: ProjectView; id: string };

const NAV = [
  { label: "Overview", href: "/portfolio-builder" },
  { label: "Opportunities", href: "/portfolio-builder/opportunities" },
  { label: "New project", href: "/portfolio-builder/projects/new" },
  { label: "Readiness", href: "/portfolio-builder/publication-readiness" },
] as const;

const HEADERS: Record<
  WorkspaceProps["view"],
  { title: string; description: string }
> = {
  dashboard: {
    title: "Portfolio Builder",
    description:
      "Turn skill gaps and trusted ebooks into projects you can back with evidence.",
  },
  opportunities: {
    title: "Portfolio opportunities",
    description:
      "Use your career target to find project ideas tied to gaps and approved sources.",
  },
  new: {
    title: "New portfolio project",
    description:
      "Define a skill, a problem to solve, and the scope of your project idea.",
  },
  readiness: {
    title: "Publication readiness",
    description:
      "Check for an approved blueprint, completed milestones, and verified evidence.",
  },
  project: {
    title: "Project workspace",
    description:
      "Plan the work, record what you built, and review the evidence behind each claim.",
  },
  architecture: {
    title: "Project architecture",
    description:
      "Review blueprint versions and the approved architecture for this project.",
  },
  artifacts: {
    title: "Project artifacts",
    description:
      "Collect project evidence and review which claims it supports.",
  },
};

export default function PortfolioWorkspace(props: WorkspaceProps) {
  return (
    <PageFrame width="wide" className="space-y-5">
      <PageHeader
        {...HEADERS[props.view]}
        eyebrow={props.view === "dashboard" ? "Build" : "Portfolio Builder"}
      />
      <SectionNav label="Portfolio Builder sections" items={NAV} />
      {"id" in props ? (
        <PortfolioProject
          key={JSON.stringify([props.view, props.id])}
          view={props.view}
          id={props.id}
        />
      ) : (
        <PortfolioBrowse key={props.view} view={props.view} />
      )}
    </PageFrame>
  );
}
