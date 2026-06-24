import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { NavSidebar } from "@/components/layout/nav-sidebar";
import { TopBar } from "@/components/layout/top-bar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CampaignPulse — AI Campaign Intelligence",
  description:
    "AI-powered campaign intelligence platform for media buyers. Unified dashboard across Google, Meta, Taboola, and TikTok.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-gray-50">
      <body className={`${inter.className} h-full`}>
        <div className="flex h-full min-h-screen">
          <NavSidebar />
          <div className="flex flex-1 flex-col">
            <TopBar />
            <main className="flex-1 p-6 overflow-auto">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
