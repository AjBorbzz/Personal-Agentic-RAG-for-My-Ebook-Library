import PortfolioWorkspace from "@/app/portfolio-builder/PortfolioWorkspace";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <PortfolioWorkspace view="project" id={projectId} />;
}
