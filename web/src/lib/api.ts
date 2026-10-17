/**
 * Return Detective — Web API Client & Data Formatter
 */

export const API_BASE = process.env.NEXT_PUBLIC_RD_API_URL || "http://localhost:8000";
export const RUNNER_BASE = process.env.NEXT_PUBLIC_RD_RUNNER_URL || "http://localhost:8001";

export interface TimelineEntry {
  timestamp: string;
  agent: string;
  title: string;
  message: string;
  status: string;
  metadata?: Record<string, any>;
}

export interface ProposedAction {
  action_id: string;
  case_id: string;
  action_type: string;
  tier: "auto" | "approve" | "recommend";
  title: string;
  description: string;
  rupee_impact: number;
  reversible: boolean;
  status: string;
  undo_url?: string;
  evidence?: Record<string, any>;
  draft_content?: string;
}

export interface EvidencePhoto {
  complaint_id: string;
  verdict: string;
  matches_claim: boolean;
  severity: number;
  photo_uri: string;
  explanation: string;
}

export interface CaseDoc {
  case_id: string;
  title: string;
  store_ids: string[];
  slice: {
    slice_key: string;
    slice_type: string;
  };
  status: "open" | "investigating" | "acting" | "awaiting_approval" | "verifying" | "closed" | "reopened" | "watching";
  finding?: {
    candidate_id: string;
    root_cause: string;
    confidence: number;
    summary_for_manager: string;
    rupee_impact: number;
  };
  hypotheses: Array<{
    cause: string;
    confidence: number;
    summary: string;
  }>;
  actions: ProposedAction[];
  rupee_lost: number;
  rupee_recovered: number;
  rupee_prevented: number;
  timeline: TimelineEntry[];
  evidence_photos: EvidencePhoto[];
  created_at: string;
  updated_at: string;
}

/** Format currency according to Indian Rupee numbering format (₹1,23,456) */
export function formatINR(val: number): string {
  if (val === undefined || val === null || isNaN(val)) return "₹0";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(val);
}

/** Translates GCS URI into public web image URL */
export function resolvePhotoUrl(photoUri?: string): string {
  if (!photoUri) return "/complaints/no_defect_bakery_1.jpg";
  const filename = photoUri.split("/complaints/")?.[1] || photoUri.split("/")?.pop() || "";
  return `/complaints/${filename}`;
}

export async function fetchCases(): Promise<CaseDoc[]> {
  try {
    const res = await fetch(`${API_BASE}/cases`, { cache: "no-store" });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("API offline; using fallback demo records", e);
  }
  return [];
}

export async function fetchCaseById(id: string): Promise<CaseDoc | null> {
  try {
    const res = await fetch(`${API_BASE}/cases/${id}`, { cache: "no-store" });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("API offline for case", id, e);
  }
  return null;
}

export async function approveCaseAction(actionId: string, approvedBy: string = "Store Manager"): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/actions/${actionId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved_by: approvedBy })
    });
    return res.ok;
  } catch (e) {
    console.error("Failed to approve action", e);
    return false;
  }
}

export async function rejectCaseAction(actionId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/actions/${actionId}/reject`, {
      method: "POST"
    });
    return res.ok;
  } catch (e) {
    console.error("Failed to reject action", e);
    return false;
  }
}

export async function triggerReplayComplaints(): Promise<boolean> {
  try {
    const res = await fetch(`${RUNNER_BASE}/run-candidates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ as_of: "2026-10-18" })
    });
    return res.ok;
  } catch (e) {
    console.error("Failed to replay complaints", e);
    return false;
  }
}

export async function triggerSimulate7Days(): Promise<boolean> {
  try {
    const res = await fetch(`${RUNNER_BASE}/simulate-days`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ days: 7 })
    });
    return res.ok;
  } catch (e) {
    console.error("Failed to simulate 7 days", e);
    return false;
  }
}

export async function triggerResetDemo(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/reset`, { method: "POST" });
    return res.ok;
  } catch (e) {
    console.error("Failed to reset demo", e);
    return false;
  }
}
