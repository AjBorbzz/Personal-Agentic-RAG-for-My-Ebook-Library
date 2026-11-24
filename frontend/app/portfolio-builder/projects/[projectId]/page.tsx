import PortfolioWorkspace from "../../PortfolioWorkspace";
export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <PortfolioWorkspace view="project" id={projectId} />;
}