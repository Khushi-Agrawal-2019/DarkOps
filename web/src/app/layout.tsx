import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import React, { Suspense } from "react";
import DemoControls from "@/components/DemoControls";
import { ShieldCheck, Search, LayoutDashboard, Inbox, Store } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DarkOps — Autonomous Dark Store Forensic Agent",
  description: "AI Builder Cup 2026 by Team SherlOps: Quick-Commerce Refund Forensic Investigation & Prevention System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Top Navigation Bar */}
        <header className="sticky top-0 z-40 bg-slate-900 text-white border-b border-slate-800 shadow-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/inbox" className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg">
                  <ShieldCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                    DarkOps
                    <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      by SherlOps
                    </span>
                  </span>
                  <span className="text-[10px] text-slate-400 block -mt-0.5">
                    Autonomous Dark Store Forensic Guard
                  </span>
                </div>
              </Link>

              <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-800">
                <Link
                  href="/inbox"
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-1.5"
                >
                  <Inbox className="w-3.5 h-3.5" />
                  Case Inbox
                </Link>
                <Link
                  href="/owner"
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-1.5"
                >
                  <LayoutDashboard className="w-3.5 h-3.5" />
                  Owner Scorecard
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
                <Store className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-medium text-white">Bengaluru Hub (4 Stores)</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Global Floating Demo Controls with Suspense */}
        <Suspense fallback={null}>
          <DemoControls />
        </Suspense>
      </body>
    </html>
  );
}
