"use client";

import { cloneElement, useId, type ReactElement, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

type FieldProps = {
  label: string;
  hint?: string;
  children: ReactElement<{ id?: string; "aria-describedby"?: string }>;
};

export function Field({ label, hint, children }: FieldProps) {
  const generatedId = useId();
  const id = children.props.id ?? generatedId;
  const hintId = `${id}-hint`;
  const descriptions = [
    children.props["aria-describedby"],
    hint && hintId,
  ].filter(Boolean);

  return (
    <div className="workspace-field-group">
      <label htmlFor={id}>{label}</label>
      {cloneElement(children, {
        id,
        "aria-describedby": descriptions.join(" ") || undefined,
      })}
      {hint && <p id={hintId}>{hint}</p>}
    </div>
  );
}

export function StatusMessage({
  tone,
  children,
}: {
  tone: "error" | "success" | "info";
  children: ReactNode;
}) {
  return (
    <div
      className={`workspace-status workspace-status--${tone}`}
      role={tone === "error" ? "alert" : "status"}
    >
      {children}
    </div>
  );
}

export function SectionNav({
  label,
  items,
}: {
  label: string;
  items: readonly { label: string; href: string }[];
}) {
  const pathname = usePathname();

  return (
    <nav aria-label={label} className="workspace-section-nav">
      {items.map(({ label: itemLabel, href }) => (
        <Link
          key={href}
          href={href}
          aria-current={pathname === href ? "page" : undefined}
        >
          {itemLabel}
        </Link>
      ))}
    </nav>
  );
}
