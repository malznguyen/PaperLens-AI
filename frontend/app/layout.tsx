import type { Metadata } from "next";
import { IBM_Plex_Sans, Newsreader } from "next/font/google";

import { AppShell } from "@/components/app-shell";

import "./globals.css";

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

const headingFont = Newsreader({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "PaperLens AI",
  description: "A workflow-first research workspace for discovering, ingesting, and analyzing scientific papers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${bodyFont.variable} ${headingFont.variable}`}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
