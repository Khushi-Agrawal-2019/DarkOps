"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Play, FastForward, RotateCcw, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react";
import { triggerReplayComplaints, triggerSimulate7Days, triggerResetDemo } from "@/lib/api";

export default function DemoControls({ onStateChange }: { onStateChange?: () => void }) {
  const searchParams = useSearchParams();
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get("demo") === "1") {
      setIsOpen(true);
    }
  }, [searchParams]);

  const handleAction = async (action: string, fn: () => Promise<boolean>, label: string) => {
    setLoading(action);
    setMessage(null);
    const ok = await fn();
    setLoading(null);
    if (ok) {
      setMessage(`✓ ${label} succeeded`);
      if (onStateChange) onStateChange();
    } else {
      setMessage(`⚠️ ${label} failed or simulated`);
      if (onStateChange) onStateChange();
    }
    setTimeout(() => setMessage(null), 4000);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {message && (
        <div className="mb-3 px-4 py-2 bg-slate-900 text-white text-xs rounded-lg shadow-xl border border-slate-700 flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{message}</span>
        </div>
      )}

      {isOpen && (
        <div className="glass-card bg-white/95 p-4 rounded-2xl shadow-2xl border border-slate-200 w-72 mb-3">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700">
                <Sparkles className="w-4 h-4" />
              </span>
              <h4 className="text-sm font-semibold text-slate-800">Hackathon Demo Rig</h4>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-600 text-xs font-medium"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2">
            <button
              id="btn-replay-complaints"
              disabled={loading !== null}
              onClick={() => handleAction("replay", triggerReplayComplaints, "Replay Complaints")}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition shadow-sm disabled:opacity-50"
            >
              <span className="flex items-center gap-2">
                <Play className="w-3.5 h-3.5" />
                Replay Complaints
              </span>
              {loading === "replay" && <span className="animate-spin">⏳</span>}
            </button>

            <button
              id="btn-simulate-7days"
              disabled={loading !== null}
              onClick={() => handleAction("simulate", triggerSimulate7Days, "+7 Days Audit")}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition shadow-sm disabled:opacity-50"
            >
              <span className="flex items-center gap-2">
                <FastForward className="w-3.5 h-3.5" />
                Simulate +7 Days
              </span>
              {loading === "simulate" && <span className="animate-spin">⏳</span>}
            </button>

            <button
              id="btn-reset-demo"
              disabled={loading !== null}
              onClick={() => handleAction("reset", triggerResetDemo, "Demo Reset")}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition disabled:opacity-50"
            >
              <span className="flex items-center gap-2">
                <RotateCcw className="w-3.5 h-3.5" />
                Reset Demo
              </span>
              {loading === "reset" && <span className="animate-spin">⏳</span>}
            </button>
          </div>

          <p className="mt-3 text-[10px] text-slate-400 text-center">
            Triggers ADK agents & Cloud Run services
          </p>
        </div>
      )}

      {!isOpen && (
        <button
          id="btn-toggle-demo"
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-slate-900 text-white text-xs font-medium shadow-2xl hover:bg-slate-800 transition border border-slate-700"
        >
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>Demo Controls</span>
        </button>
      )}
    </div>
  );
}
