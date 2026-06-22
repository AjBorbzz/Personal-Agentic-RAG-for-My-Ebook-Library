import Link from "next/link";

type PageHeaderProps = {
  title: string;
  description: string;
};

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <Link href="/" className="text-sm text-neutral-400 hover:text-white">
        ← Back to dashboard
      </Link>

      <h1 className="mt-4 text-3xl font-bold text-white">{title}</h1>

      <p className="mt-3 max-w-3xl text-neutral-400">{description}</p>
    </div>
  );
}