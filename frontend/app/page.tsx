import Image from "next/image";
import Link from "next/link";
import { PageFrame } from "@/components/PageHeader";
import { ToolCard } from "@/components/ToolCard";
import { WorkspaceIcon } from "@/components/WorkspaceIcon";
import { workspaceGroups } from "@/components/workspace-navigation";
import styles from "./home.module.css";

export default function HomePage() {
  return (
    <PageFrame width="wide" className={styles.home}>
      <section className={styles.hero} aria-labelledby="workspace-title">
        <div className={styles.heroImage} aria-hidden="true">
          <Image
            src="/ebook-archive.webp"
            alt=""
            fill
            sizes="(max-width: 650px) 100vw, 58vw"
            preload
          />
        </div>
        <div className={styles.heroContent}>
          <p className="workspace-kicker">Personal ebook workspace</p>
          <h1 id="workspace-title">Put your ebook library to work.</h1>
          <p className={styles.intro}>
            Search your books, ask questions with citations, and turn what you
            learn into portfolio projects.
          </p>
          <div className={styles.heroActions}>
            <Link href="/search" className="workspace-button">
              <WorkspaceIcon name="search" />
              Search ebooks
            </Link>
            <Link
              href="/documents"
              className="workspace-button workspace-button--secondary"
            >
              Browse library
            </Link>
          </div>
        </div>
      </section>

      <section aria-labelledby="workspace-tools" className={styles.directory}>
        <h2 id="workspace-tools">Workspace tools</h2>
        <div className={styles.shelves}>
          {workspaceGroups.map(({ label, icon, tools }) => (
            <section key={label} className={styles.shelf} aria-label={label}>
              <h3>
                <span>
                  <WorkspaceIcon name={icon} />
                </span>
                {label}
              </h3>
              <ul>
                {tools.map(({ title, href }) => (
                  <li key={href}>
                    <ToolCard title={title} href={href} />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </section>
    </PageFrame>
  );
}
