import {
  GitCompareArrows,
  LayoutDashboard,
  LibraryBig,
  MessagesSquare,
  Search,
} from "lucide-react";

import type { NavigationItem } from "@/types/navigation";

export const navigationItems: NavigationItem[] = [
  {
    title: "Dashboard",
    href: "/",
    description: "Workspace overview",
    icon: LayoutDashboard,
  },
  {
    title: "Search Papers",
    href: "/search",
    description: "Discover literature",
    icon: Search,
  },
  {
    title: "Paper Workspace",
    href: "/workspace",
    description: "Track ingestion",
    icon: LibraryBig,
  },
  {
    title: "Research Chat",
    href: "/chat",
    description: "Grounded Q&A",
    icon: MessagesSquare,
  },
  {
    title: "Compare Papers",
    href: "/compare",
    description: "Structured comparison",
    icon: GitCompareArrows,
  },
];
