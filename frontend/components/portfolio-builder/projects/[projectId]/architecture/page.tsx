import PortfolioWorkspace from "../../../../../components/portfolio-builder/PortfolioWorkspace";
export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <PortfolioWorkspace view="architecture" id={projectId} />;
}