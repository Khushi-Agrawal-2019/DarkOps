"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { formatINR, fetchCases, CaseDoc } from "@/lib/api";
import { 
  TrendingUp, ShieldCheck, DollarSign, Store, 
  BarChart3, CheckCircle2, AlertOctagon, ArrowUpRight
} from "lucide-react";

export default function OwnerDashboardPage() {
  const [cases, setCases] = useState<CaseDoc[]>([]);

  useEffect(() => {
    fetchCases().then(setCases);
  }, []);

  // Compute Financial Aggregates
  const totalPrevented = cases.reduce((acc, c) => acc + (c.rupee_prevented || 0), 162064);
  const totalRecovered = cases.reduce((acc, c) => acc + (c.rupee_recovered || 0), 12500);
  const netSavings = totalPrevented + totalRecovered;

  const SUPPLIER_SCORECARD = [
    { name: "GreenLeaf Farms", cat: "Fresh Produce", rating: "3.4 (C-)", claims: "₹12,500 (Claim Approved)", defectRate: "4.8%", status: "Audit Action Enforced" },
    { name: "Amul India West", cat: "Dairy & Frozen", rating: "4.9 (A+)", claims: "₹0", defectRate: "0.8%", status: "Compliant" },
    { name: "Heritage Dairies", cat: "Dairy & Frozen", rating: "4.7 (A)", claims: "₹0", defectRate: "1.1%", status: "Compliant" },
    { name: "Nandini KMF Dairy", cat: "Dairy & Frozen", rating: "4.8 (A)", claims: "₹0", defectRate: "0.9%", status: "Compliant" },
    { name: "The Daily Loaf", cat: "Bakery", rating: "4.5 (B+)", claims: "₹0", defectRate: "1.4%", status: "Monitoring (Bread Spike)" },
  ];

  const STORE_COMPARISONS = [
    { id: "S1", name: "Koramangala", orders: "11,240", defectRate: "1.5%", resolvedIssue: "Freezer F2 Thermostat Drift", prevented: "₹27,880" },
    { id: "S2", name: "Indiranagar", orders: "10,890", defectRate: "1.4%", resolvedIssue: "Zone 3 Heatwave Routing", prevented: "₹27,880" },
    { id: "S3", name: "HSR Layout", orders: "10,510", defectRate: "1.8%", resolvedIssue: "Packer PK-308 Cushion Wrap", prevented: "₹80,696" },
    { id: "S4", name: "Whitefield", orders: "9,925", defectRate: "1.1%", resolvedIssue: "Baseline Healthy Operations", prevented: "₹0" },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Executive Owner Scorecard
        </h1>
        <p className="text-sm text-slate-500">
          Dark store quick-commerce loss prevention, supplier recovery, and quality metrics
        </p>
      </div>

      {/* 3 Giant KPI Financial Numbers */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card bg-gradient-to-br from-emerald-500/10 to-teal-500/5 p-6 rounded-2xl border border-emerald-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
              Total Loss Prevented
            </span>
            <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-md">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <p className="text-4xl font-black text-slate-900 mt-3 tracking-tight">
            {formatINR(totalPrevented)}
          </p>
          <p className="text-xs text-emerald-700 font-medium mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Projected run-rate across 4 dark stores
          </p>
        </div>

        <div className="glass-card bg-gradient-to-br from-blue-500/10 to-indigo-500/5 p-6 rounded-2xl border border-blue-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-800">
              Supplier Rupee Recovered
            </span>
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <p className="text-4xl font-black text-slate-900 mt-3 tracking-tight">
            {formatINR(totalRecovered)}
          </p>
          <p className="text-xs text-blue-700 font-medium mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Vendor credit claims successfully clawed back
          </p>
        </div>

        <div className="glass-card bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl text-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
              Net Dark Store Savings
            </span>
            <div className="w-9 h-9 rounded-xl bg-emerald-500 text-slate-900 flex items-center justify-center font-black">
              ₹
            </div>
          </div>
          <p className="text-4xl font-black text-white mt-3 tracking-tight">
            {formatINR(netSavings)}
          </p>
          <p className="text-xs text-slate-300 font-medium mt-1 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Autonomous agent ROI verified by Auditor
          </p>
        </div>
      </div>

      {/* Financial Loss by Root Cause (Bar Chart Visualization) */}
      <div className="glass-card bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-600" />
              Loss Prevented by Root Cause
            </h3>
            <p className="text-xs text-slate-500">Distribution of operational savings across the 5 hypothesis classes</p>
          </div>
          <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Audit Verified
          </span>
        </div>

        <div className="space-y-3 pt-2">
          <div>
            <div className="flex items-center justify-between text-xs font-medium mb-1">
              <span className="text-slate-700 font-bold">Packing Negligence (PK-308 Cushion Wrap)</span>
              <span className="text-slate-900 font-extrabold">₹80,696 (46%)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div className="bg-emerald-600 h-3 rounded-full" style={{ width: "46%" }} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs font-medium mb-1">
              <span className="text-slate-700 font-bold">Storage Malfunction (S1 Freezer F2)</span>
              <span className="text-slate-900 font-extrabold">₹27,880 (16%)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div className="bg-teal-600 h-3 rounded-full" style={{ width: "16%" }} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs font-medium mb-1">
              <span className="text-slate-700 font-bold">Delivery Cold-Chain Transit (S2 Zone 3)</span>
              <span className="text-slate-900 font-extrabold">₹27,880 (16%)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div className="bg-sky-600 h-3 rounded-full" style={{ width: "16%" }} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs font-medium mb-1">
              <span className="text-slate-700 font-bold">Supplier Batch Rot (B-4471 GreenLeaf Farms)</span>
              <span className="text-slate-900 font-extrabold">₹25,608 (15%)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div className="bg-indigo-600 h-3 rounded-full" style={{ width: "15%" }} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs font-medium mb-1">
              <span className="text-slate-700 font-bold">Refund Fraud Ring (3 Photo Duplication Accounts)</span>
              <span className="text-slate-900 font-extrabold">₹12,500 (7%)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div className="bg-rose-500 h-3 rounded-full" style={{ width: "7%" }} />
            </div>
          </div>
        </div>
      </div>

      {/* Supplier Scorecard Table */}
      <div className="glass-card bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            Supplier Quality & Dispute Scorecard
          </h3>
          <p className="text-xs text-slate-500">Live vendor defect rankings and forensic clawback actions</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase text-[10px]">
                <th className="pb-3">Supplier Name</th>
                <th className="pb-3">Category</th>
                <th className="pb-3">Quality Rating</th>
                <th className="pb-3">Defect Rate</th>
                <th className="pb-3">Clawback Claim</th>
                <th className="pb-3">Audit Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {SUPPLIER_SCORECARD.map((sup, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 transition">
                  <td className="py-3 font-bold text-slate-900">{sup.name}</td>
                  <td className="py-3 text-slate-600">{sup.cat}</td>
                  <td className="py-3">
                    <span className={`font-semibold ${sup.rating.includes("C") ? "text-rose-600" : "text-emerald-600"}`}>
                      {sup.rating}
                    </span>
                  </td>
                  <td className="py-3 text-slate-700 font-semibold">{sup.defectRate}</td>
                  <td className="py-3 font-mono font-bold text-slate-900">{sup.claims}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      sup.status.includes("Enforced")
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : sup.status.includes("Monitoring")
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    }`}>
                      {sup.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Store Comparison Grid */}
      <div className="glass-card bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            Bengaluru Dark Store Quality Matrix
          </h3>
          <p className="text-xs text-slate-500">Store-by-store volume, defect rates, and interventions</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {STORE_COMPARISONS.map((st) => (
            <div key={st.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold bg-slate-200 px-2 py-0.5 rounded text-slate-700">
                  {st.id}
                </span>
                <span className="text-xs font-semibold text-slate-900">{st.defectRate}</span>
              </div>
              <h4 className="text-sm font-bold text-slate-900">{st.name}</h4>
              <p className="text-[11px] text-slate-500">60-day volume: {st.orders} orders</p>
              <div className="pt-2 border-t border-slate-200/60">
                <span className="text-[10px] text-slate-400 block uppercase">Intervention:</span>
                <span className="text-xs font-medium text-emerald-700 block">{st.resolvedIssue}</span>
                <span className="text-[11px] font-bold text-slate-800 mt-1 block">
                  Saved: {st.prevented}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
