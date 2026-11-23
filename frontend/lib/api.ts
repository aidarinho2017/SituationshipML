import { Analysis, Preview, SavedAnalysis, SavedAnalysisSummary } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API}${path}`, { method: "POST", body });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || "The analysis service could not process this export.");
  }
  return response.json();
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || "The analysis service could not complete this request.");
  }
  return response.status === 204 ? undefined as T : response.json();
}

export function parseChat(file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<Preview>("/api/chat/parse", body);
}

export function analyzeChat(file: File, participants: string[], gap: number) {
  const body = new FormData();
  body.append("file", file);
  body.append("participant_a", participants[0]);
  body.append("participant_b", participants[1]);
  body.append("session_gap_hours", String(gap));
  return request<Analysis>("/api/chat/analyze", body);
}

export function saveAnalysis(analysis: Analysis) {
  return api<SavedAnalysis>("/api/analyses", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(analysis),
  });
}

export function listAnalyses() {
  return api<SavedAnalysisSummary[]>("/api/analyses");
}

export function getAnalysis(id: string) {
  return api<SavedAnalysis>(`/api/analyses/${id}`);
}

export function renameAnalysis(id: string, title: string) {
  return api<SavedAnalysisSummary>(`/api/analyses/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }),
  });
}

export function deleteAnalysis(id: string) {
  return api<void>(`/api/analyses/${id}`, { method: "DELETE" });
}

