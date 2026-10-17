"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  fetchCases, formatINR, CaseDoc 
} from "@/lib/api";
import { 
  AlertTriangle, ShieldAlert, CheckCircle2, Clock, 
  Store, ArrowRight, Eye, Sparkles, Filter, ChevronRight
} from "lucide-react";

const STORE_OPTIONS = [
  { id: "ALL", name: "All Dark Stores" },
  { id: "S1", name: "S1 Koramangala" },
  { id: "S2", name: "S2 Indiranagar" },
  { id: "S3", name: "S3 HSR Layout" },
  { id: "S4", name: "S4 Whitefield" },
];

export default function InboxPage() {
  const [cases, setCases] = useState<CaseDoc[]>([]);
  const [selectedStore, setSelectedStore] = useState("ALL");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    const data = await fetchCases();
    // Sort by rupees at risk descending
    data.sort((a, b) => (b.rupee_lost || 0) - (a.rupee_lost || 0));
    setCases(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    // Live polling listener every 2.5 seconds
    const interval = setInterval(loadData, 2500);
    return () => clearInterval(interval);
  }, []);

  // Filter by store
  const filteredCases = cases.filter((c) => {
    if (selectedStore === "ALL") return true;
    return c.store_ids && c.store_ids.some((s) => s.includes(selectedStore));
  });

  // Calculate 3 Top Bar Totals
  const openCasesCount = cases.filter((c) => c.status !== "closed").length;
  const totalRupeesAtRisk = cases
    .filter((c) => c.status !== "closed")
    .reduce((acc, curr) => acc + (curr.rupee_lost || 0), 0);
  const approvalsWaitingCount = cases.reduce((acc, curr) => {
    const pending = (curr.actions || []).filter((a) => a.status === "awaiting_approval");
    return acc + pending.length;
  }, 0);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "awaiting_approval":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
            <AlertTriangle className="w-3 h-3" />
            Needs Approval
          </span>
        );
      case "verifying":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
            <Clock className="w-3 h-3" />
            Verifying (7d)
          </span>
        );
      case "closed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            Closed & Resolved
          </span>
        );
      case "watching":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-300">
            <Eye className="w-3 h-3" />
            Watching (Inconclusive)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Sparkles className="w-3 h-3" />
            Investigating
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar with Store Picker & Summary Cards */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Dark Store Forensic Inbox
          </h1>
          <p className="text-sm text-slate-500">
            Autonomous multi-agent complaint clustering & root-cause resolution
          </p>
        </div>

        {/* Store Picker */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            id="store-picker"
            value={selectedStore}
            onChange={(e) => setSelectedStore(e.target.value)}
            className="px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs font-medium text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {STORE_OPTIONS.map((st) => (
              <option key={st.id} value={st.id}>
                {st.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Three Metric Totals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card p-5 rounded-2xl shadow-sm border border-slate-200 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Open Cases
            </p>
            <p className="text-3xl font-extrabold text-slate-900 mt-1">
              {openCasesCount}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl shadow-sm border border-slate-200 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Rupees at Risk
            </p>
            <p className="text-3xl font-extrabold text-slate-900 mt-1">
              {formatINR(totalRupeesAtRisk)}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <span className="text-xl font-bold">₹</span>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl shadow-sm border border-slate-200 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Approvals Waiting
            </p>
            <p className="text-3xl font-extrabold text-amber-600 mt-1">
              {approvalsWaitingCount}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Case List Header */}
      <div className="flex items-center justify-between pt-2">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          Clustered Cases ({filteredCases.length})
        </h2>
        <span className="text-xs text-slate-400">Sorted by Rupees at Risk</span>
      </div>

      {/* List of Case Cards */}
      <div className="space-y-3">
        {loading && cases.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">
            <div className="w-8 h-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm">Connecting to Return Detective agents...</p>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200">
            <p className="font-medium">No open cases found for selected store.</p>
            <p className="text-xs text-slate-400 mt-1">Click &apos;Replay Complaints&apos; in Demo Controls to simulate live returns.</p>
          </div>
        ) : (
          filteredCases.map((c) => {
            const confidence = c.finding?.confidence || 0.92;
            return (
              <Link
                key={c.case_id}
                href={`/cases/${c.case_id}`}
                className="block group"
              >
                <div className="glass-card bg-white hover:bg-slate-50/80 p-5 rounded-2xl border border-slate-200/90 shadow-sm transition hover:shadow-md hover:border-emerald-300">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1.5 max-w-2xl">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                          {c.case_id}
                        </span>
                        {getStatusBadge(c.status)}
                        {c.store_ids && c.store_ids.map((st) => (
                          <span
                            key={st}
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md"
                          >
                            <Store className="w-3 h-3 text-slate-400" />
                            {st}
                          </span>
                        ))}
                      </div>

                      <h3 className="text-base font-semibold text-slate-900 group-hover:text-emerald-700 transition">
                        {c.title}
                      </h3>

                      {c.finding?.summary_for_manager && (
                        <p className="text-xs text-slate-500 line-clamp-1">
                          {c.finding.summary_for_manager}
                        </p>
                      )}
                    </div>

                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100">
                      <div className="text-right">
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                          Rupee Impact
                        </span>
                        <span className="text-lg font-bold text-slate-900">
                          {formatINR(c.rupee_lost)}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 mt-1">
                        <div className="text-right">
                          <span className="text-[10px] text-slate-400 block">Certainty</span>
                          <span className="text-xs font-semibold text-emerald-600">
                            {(confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition" />
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })
        )}
      </div>
    </div>
  );
}
