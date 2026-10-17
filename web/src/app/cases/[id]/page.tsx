"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  fetchCaseById, approveCaseAction, rejectCaseAction, 
  formatINR, resolvePhotoUrl, CaseDoc 
} from "@/lib/api";
import { 
  ArrowLeft, ShieldCheck, AlertTriangle, CheckCircle2, 
  Clock, Eye, Sparkles, Store, Check, X, Undo2, 
  FileText, ExternalLink, Activity, Image as ImageIcon,
  Flame, ThermometerSnowflake, PackageCheck, Truck
} from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [caseDoc, setCaseDoc] = useState<CaseDoc | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showDraft, setShowDraft] = useState<string | null>(null);

  const loadCase = async () => {
    const data = await fetchCaseById(caseId);
    if (data) {
      setCaseDoc(data);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadCase();
    const interval = setInterval(loadCase, 2500);
    return () => clearInterval(interval);
  }, [caseId]);

  const handleApprove = async (actionId: string) => {
    setActionLoading(actionId);
    await approveCaseAction(actionId, "Store Manager (Web Approval)");
    await loadCase();
    setActionLoading(null);
  };

  const handleReject = async (actionId: string) => {
    setActionLoading(actionId);
    await rejectCaseAction(actionId);
    await loadCase();
    setActionLoading(null);
  };

  if (loading && !caseDoc) {
    return (
      <div className="p-16 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p>Loading forensic case file {caseId}...</p>
      </div>
    );
  }

  if (!caseDoc) {
    return (
      <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
        <h2 className="text-lg font-bold text-slate-800">Case Not Found</h2>
        <p className="text-sm text-slate-500 mt-1">Case {caseId} could not be retrieved from store records.</p>
        <Link href="/inbox" className="inline-block mt-4 text-xs font-semibold text-emerald-600 hover:underline">
          ← Return to Case Inbox
        </Link>
      </div>
    );
  }

  const rootCause = caseDoc.finding?.root_cause || "";

  return (
    <div className="space-y-6">
      {/* Top Navigation & Back Link */}
      <div className="flex items-center justify-between">
        <Link
          href="/inbox"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Case Inbox
        </Link>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>Case ID:</span>
          <span className="font-mono font-bold text-slate-700 bg-slate-200/60 px-2 py-0.5 rounded">
            {caseDoc.case_id}
          </span>
        </div>
      </div>

      {/* Case Header Card */}
      <div className="glass-card bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              {caseDoc.store_ids && caseDoc.store_ids.map((st) => (
                <span
                  key={st}
                  className="inline-flex items-center gap-1 text-xs font-medium text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded-md"
                >
                  <Store className="w-3.5 h-3.5 text-slate-500" />
                  {st}
                </span>
              ))}
              <span className="text-xs font-semibold uppercase px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                Status: {caseDoc.status.replace("_", " ")}
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              {caseDoc.title}
            </h1>
            {caseDoc.finding?.summary_for_manager && (
              <p className="text-sm text-slate-600 max-w-3xl">
                {caseDoc.finding.summary_for_manager}
              </p>
            )}
          </div>

          <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                Rupees at Risk
              </span>
              <span className="text-xl font-black text-rose-600">
                {formatINR(caseDoc.rupee_lost)}
              </span>
            </div>
            {caseDoc.rupee_prevented > 0 && (
              <div className="border-l border-slate-200 pl-4">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Loss Prevented
                </span>
                <span className="text-xl font-black text-emerald-600">
                  {formatINR(caseDoc.rupee_prevented)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3-Column Core Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* ================================================================= */}
        {/* Column 1: Evidence (Left) */}
        {/* ================================================================= */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-emerald-600" />
              Complaint Evidence
            </h2>
            <span className="text-[11px] text-slate-400 font-medium">Gemini Flash Multimodal</span>
          </div>

          {/* Complaint Photos Grid with Gemini Verdict Badges */}
          <div className="space-y-3">
            {caseDoc.evidence_photos && caseDoc.evidence_photos.length > 0 ? (
              caseDoc.evidence_photos.map((ep, idx) => (
                <div
                  key={idx}
                  className="glass-card bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm"
                >
                  <div className="relative h-44 bg-slate-100 overflow-hidden">
                    <img
                      src={resolvePhotoUrl(ep.photo_uri)}
                      alt={`Complaint return ${ep.complaint_id}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = "none";
                      }}
                    />
                    <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] font-mono font-bold bg-slate-900/80 text-white px-2 py-0.5 rounded backdrop-blur">
                        {ep.complaint_id}
                      </span>
                      {ep.matches_claim ? (
                        <span className="text-[10px] font-semibold bg-emerald-600/90 text-white px-2 py-0.5 rounded backdrop-blur flex items-center gap-1">
                          <Check className="w-2.5 h-2.5" />
                          Verified: {ep.verdict} (Sev {ep.severity}/5)
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold bg-rose-600/90 text-white px-2 py-0.5 rounded backdrop-blur flex items-center gap-1">
                          <X className="w-2.5 h-2.5" />
                          No Defect Found
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="p-3 text-xs text-slate-600 border-t border-slate-100">
                    <p className="font-medium text-slate-800">{ep.explanation}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-xs text-slate-400 bg-white rounded-xl border border-slate-200">
                No complaint photographs attached to candidate cluster.
              </div>
            )}
          </div>
        </div>

        {/* ================================================================= */}
        {/* Column 2: Hypotheses (Middle) */}
        {/* ================================================================= */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              Hypotheses Panel (5 Parallel)
            </h2>
            <span className="text-[11px] text-slate-400 font-medium">Gemini Pro Detective</span>
          </div>

          <div className="space-y-3">
            {caseDoc.hypotheses && caseDoc.hypotheses.map((h, idx) => {
              const isWinner = h.cause === rootCause && rootCause !== "inconclusive";
              const isRuledOut = h.confidence < 0.30;
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border transition ${
                    isWinner
                      ? "gradient-winner shadow-md"
                      : isRuledOut
                      ? "gradient-ruled-out"
                      : "bg-white border-slate-200 shadow-sm"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900 capitalize">
                        {h.cause.replace("_", " ")}
                      </span>
                      {isWinner && (
                        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-600 text-white shadow-sm flex items-center gap-1">
                          <ShieldCheck className="w-2.5 h-2.5" />
                          Root Cause
                        </span>
                      )}
                    </div>
                    <span className={`text-xs font-extrabold ${isWinner ? "text-emerald-700" : "text-slate-700"}`}>
                      {(h.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* Confidence Bar */}
                  <div className="w-full bg-slate-200 rounded-full h-2 mb-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-700 ${
                        isWinner ? "bg-emerald-600" : isRuledOut ? "bg-slate-400" : "bg-blue-600"
                      }`}
                      style={{ width: `${Math.max(5, h.confidence * 100)}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    {h.summary}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* ================================================================= */}
        {/* Column 3: Actions (Right) */}
        {/* ================================================================= */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Enforcer Actions
            </h2>
            <span className="text-[11px] text-slate-400 font-medium">Deterministic Guardrails</span>
          </div>

          <div className="space-y-3">
            {caseDoc.actions && caseDoc.actions.length > 0 ? (
              caseDoc.actions.map((act) => {
                const isPending = act.status === "awaiting_approval";
                const isDone = act.status === "Done" || act.status === "COMPLETED";

                return (
                  <div
                    key={act.action_id}
                    className={`p-4 rounded-xl border bg-white shadow-sm space-y-3 ${
                      isPending ? "border-amber-300 ring-2 ring-amber-100" : "border-slate-200"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                          act.tier === "auto"
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                            : act.tier === "approve"
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-indigo-100 text-indigo-800 border border-indigo-200"
                        }`}
                      >
                        {act.tier === "auto" ? "Auto" : act.tier === "approve" ? "Needs Approval" : "Recommended"}
                      </span>

                      <span
                        className={`text-[10px] font-semibold ${
                          isDone
                            ? "text-emerald-600 flex items-center gap-1"
                            : isPending
                            ? "text-amber-600 animate-pulse font-bold"
                            : "text-slate-500"
                        }`}
                      >
                        {isDone && <Check className="w-3 h-3" />}
                        {act.status}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{act.title}</h4>
                      <p className="text-[11px] text-slate-500 mt-1">{act.description}</p>
                    </div>

                    {act.rupee_impact > 0 && (
                      <div className="text-[11px] font-medium text-slate-600">
                        Rupee Value: <span className="font-bold text-slate-900">{formatINR(act.rupee_impact)}</span>
                      </div>
                    )}

                    {/* Expandable Draft Claim Content */}
                    {act.draft_content && (
                      <div className="pt-1">
                        <button
                          onClick={() => setShowDraft(showDraft === act.action_id ? null : act.action_id)}
                          className="text-[11px] text-emerald-700 font-semibold hover:underline flex items-center gap-1"
                        >
                          <FileText className="w-3 h-3" />
                          {showDraft === act.action_id ? "Hide Draft Letter" : "View Vendor Claim Notice"}
                        </button>
                        {showDraft === act.action_id && (
                          <pre className="mt-2 p-3 bg-slate-900 text-slate-200 text-[10px] rounded-lg font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                            {act.draft_content}
                          </pre>
                        )}
                      </div>
                    )}

                    {/* One-Tap Approve / Reject Buttons for Pending Actions */}
                    {isPending && (
                      <div className="pt-2 flex items-center gap-2 border-t border-slate-100">
                        <button
                          id={`btn-approve-${act.action_id}`}
                          disabled={actionLoading === act.action_id}
                          onClick={() => handleApprove(act.action_id)}
                          className="flex-1 py-1.5 px-3 rounded-lg text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 transition flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          Approve Action
                        </button>
                        <button
                          id={`btn-reject-${act.action_id}`}
                          disabled={actionLoading === act.action_id}
                          onClick={() => handleReject(act.action_id)}
                          className="py-1.5 px-3 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="p-6 text-center text-xs text-slate-400 bg-white rounded-xl border border-slate-200">
                No operational actions required for this case.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* =================================================================== */}
      {/* Bottom: The Agent Timeline */}
      {/* =================================================================== */}
      <div className="glass-card bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-600" />
            Agent Chronological Timeline
          </h3>
          <span className="text-xs text-slate-400">Live Agent Event Stream</span>
        </div>

        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
          {caseDoc.timeline && caseDoc.timeline.map((item, idx) => (
            <div key={idx} className="relative group">
              <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-emerald-500 ring-4 ring-white" />
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[10px] font-mono text-slate-400">
                  {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  {item.agent.replace("_", " ")}
                </span>
                <h4 className="text-xs font-bold text-slate-900">{item.title}</h4>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed pl-0.5">
                {item.message}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
