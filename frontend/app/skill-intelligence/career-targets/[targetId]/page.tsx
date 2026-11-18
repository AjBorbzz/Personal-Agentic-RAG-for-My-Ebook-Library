"use client";
import { useParams } from "next/navigation";
import SkillWorkspace from "../../../../components/skill-intelligence/SkillWorkspace";
export default function Page() {
  const params = useParams<{targetId: string}>();
  return <SkillWorkspace mode="target" targetId={params.targetId} />;
}