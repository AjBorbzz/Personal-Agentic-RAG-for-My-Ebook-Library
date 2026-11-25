import SkillWorkspace from "@/components/skill-intelligence/SkillWorkspace";

export default async function Page({
  params,
}: {
  params: Promise<{ skillId: string }>;
}) {
  const { skillId } = await params;
  return <SkillWorkspace mode="skill" skillId={skillId} />;
}
