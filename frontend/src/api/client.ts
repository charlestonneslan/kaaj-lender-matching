import type {
  ApplicationCreate,
  ApplicationRead,
  ApplicationSummary,
  Lender,
  MatchResult,
  Program,
  Rule,
} from "../types";

export type LenderCreate = Omit<Lender, "id" | "active" | "programs"> & {
  active?: boolean;
  programs?: Array<Omit<Program, "id" | "rules"> & { rules?: Array<Omit<Rule, "id" | "program_id">> }>;
};

export type ProgramCreate = Omit<Program, "id" | "rules"> & {
  rules?: Array<Omit<Rule, "id" | "program_id">>;
};

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  listApplications: () => request<ApplicationSummary[]>("/applications"),
  getApplication: (id: number) => request<ApplicationRead>(`/applications/${id}`),
  createApplication: (body: ApplicationCreate) =>
    request<ApplicationRead>("/applications", { method: "POST", body: JSON.stringify(body) }),
  updateApplication: (id: number, body: ApplicationCreate) =>
    request<ApplicationRead>(`/applications/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  evaluate: (id: number) =>
    request<MatchResult[]>(`/applications/${id}/evaluate`, { method: "POST" }),
  getResults: (id: number) => request<MatchResult[]>(`/applications/${id}/results`),

  listLenders: () => request<Lender[]>("/lenders"),
  getLender: (id: number) => request<Lender>(`/lenders/${id}`),
  createLender: (body: LenderCreate) =>
    request<Lender>("/lenders", { method: "POST", body: JSON.stringify(body) }),
  addProgram: (lenderId: number, body: ProgramCreate) =>
    request<Program>(`/lenders/${lenderId}/programs`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateRule: (id: number, body: Omit<Rule, "id" | "program_id">) =>
    request<Rule>(`/lenders/rules/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteRule: (id: number) =>
    request<void>(`/lenders/rules/${id}`, { method: "DELETE" }),
  addRule: (programId: number, body: Omit<Rule, "id" | "program_id">) =>
    request<Rule>(`/lenders/programs/${programId}/rules`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
