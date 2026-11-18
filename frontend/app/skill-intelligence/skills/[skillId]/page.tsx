"use client";
import { useParams } from "next/navigation";
import SkillWorkspace from "../../../../components/skill-intelligence/SkillWorkspace";
export default function Page() {
  const params = useParams<{skillId: string}>();
  return <SkillWorkspace mode="skill" skillId={params.skillId} />;
}