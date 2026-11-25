import type { ReactNode } from "react";
import { SkillProfileProvider } from "@/components/skill-intelligence/SkillProfiles";

export default function Layout({ children }: { children: ReactNode }) {
  return <SkillProfileProvider>{children}</SkillProfileProvider>;
}
