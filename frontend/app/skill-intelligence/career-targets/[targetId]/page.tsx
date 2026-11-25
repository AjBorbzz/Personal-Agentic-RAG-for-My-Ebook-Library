import SkillWorkspace from "@/components/skill-intelligence/SkillWorkspace";

export default async function Page({
  params,
}: {
  params: Promise<{ targetId: string }>;
}) {
  const { targetId } = await params;
  return <SkillWorkspace mode="target" targetId={targetId} />;
}
