import type { Metadata } from "next";
import localFont from "next/font/local";
import { WorkspaceHeader } from "@/components/WorkspaceHeader";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/geist-latin.woff2",
  variable: "--font-geist-sans",
  weight: "100 900",
  display: "swap",
});

const geistMono = localFont({
  src: "./fonts/geist-mono-latin.woff2",
  variable: "--font-geist-mono",
  weight: "100 900",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Personal Agentic RAG for My Ebooks",
  description:
    "A personal ebook workspace for source-backed search, technical learning, and portfolio work.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <WorkspaceHeader />
        {children}
      </body>
    </html>
  );
}
