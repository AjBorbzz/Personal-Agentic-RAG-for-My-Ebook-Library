import type { ReactNode } from "react";
import Link from "next/link";

type PageFrameProps = {
  children: ReactNode;
  width?: "default" | "wide" | "narrow";
  className?: string;
};

export function PageFrame({
  children,
  width = "default",
  className = "",
}: PageFrameProps) {
  return (
    <main
      id="main-content"
      tabIndex={-1}
      className={`page-frame page-frame--${width} ${className}`.trim()}
    >
      {children}
    </main>
  );
}

type PageHeaderProps = {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children?: ReactNode;
  back?: { label: string; href: string };
};

export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  children,
  back,
}: PageHeaderProps) {
  return (
    <header className="page-heading">
      {back && (
        <Link href={back.href} className="page-back">
          {back.label}
        </Link>
      )}
      <div className="page-heading-row">
        <div className="min-w-0">
          {eyebrow && <p className="workspace-kicker">{eyebrow}</p>}
          <h1>{title}</h1>
          {description && <p className="page-description">{description}</p>}
        </div>
        {actions && <div className="page-heading-actions">{actions}</div>}
      </div>
      {children}
    </header>
  );
}
