"use client";

import {
  BarChart3,
  DollarSign,
  FileText,
  Globe,
  LayoutDashboard,
  Lightbulb,
  Megaphone,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/creatives", label: "Creative Analyzer", icon: FileText },
  { href: "/budget", label: "Budget Optimizer", icon: DollarSign },
  { href: "/landing-pages", label: "Landing Pages", icon: Globe },
  { href: "/insights", label: "Insights", icon: Lightbulb },
];

export function NavSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
        <BarChart3 className="h-7 w-7 text-blue-600" />
        <span className="text-lg font-bold text-gray-900">CampaignPulse</span>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-gray-200 p-4">
        <div className="rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 p-3 text-white">
          <p className="text-xs font-medium">AI Campaign Intelligence</p>
          <p className="mt-1 text-[10px] opacity-80">v0.1.0</p>
        </div>
      </div>
    </aside>
  );
}
