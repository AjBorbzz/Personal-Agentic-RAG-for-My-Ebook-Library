import Link from "next/link";
import { WorkspaceIcon } from "./WorkspaceIcon";

export function ToolCard({ title, href }: { title: string; href: string }) {
  return (
    <Link href={href} className="tool-link">
      {title}
      <WorkspaceIcon name="chevron" />
    </Link>
  );
}
