import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { MatchResult, RuleEvaluation } from "../types";

export default function ApplicationDetail() {
  const { id } = useParams();
  const appId = Number(id);
  const qc = useQueryClient();

  const appQ = useQuery({
    queryKey: ["application", appId],
    queryFn: () => api.getApplication(appId),
    enabled: !Number.isNaN(appId),
  });

  const resultsQ = useQuery({
    queryKey: ["results", appId],
    queryFn: () => api.getResults(appId),
    enabled: !Number.isNaN(appId),
  });

  const evalMut = useMutation({
    mutationFn: () => api.evaluate(appId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["results", appId] });
      qc.invalidateQueries({ queryKey: ["application", appId] });
    },
  });

  if (appQ.isLoading) return <p>Loading…</p>;
  if (appQ.error || !appQ.data) return <p className="text-red-600">Application not found</p>;
  const app = appQ.data;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded p-5">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-lg font-semibold">
              {app.borrower?.legal_name ?? `Application #${app.id}`}
            </h2>
            <p className="text-sm text-slate-500">
              {app.borrower?.industry} · {app.borrower?.state} ·{" "}
              {app.borrower?.years_in_business}y in business
            </p>
          </div>
          <button
            onClick={() => evalMut.mutate()}
            disabled={evalMut.isPending}
            className="bg-slate-900 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {evalMut.isPending ? "Re-running…" : "Re-evaluate"}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
          <Stat label="FICO" value={app.guarantor?.fico} />
          <Stat label="PayNet" value={app.business_credit?.paynet_score ?? "—"} />
          <Stat
            label="Loan amount"
            value={
              app.loan_request?.amount ? `$${app.loan_request.amount.toLocaleString()}` : "—"
            }
          />
          <Stat label="Term" value={`${app.loan_request?.term_months ?? "?"} mo`} />
        </div>
      </div>

      <h2 className="text-lg font-semibold">Lender matches</h2>
      {resultsQ.isLoading ? <p>Loading results…</p> : null}
      <div className="space-y-3">
        {(resultsQ.data ?? []).map((r) => (
          <LenderCard key={r.id} result={r} />
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-slate-500 text-xs uppercase tracking-wide">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

function LenderCard({ result }: { result: MatchResult }) {
  const [open, setOpen] = useState(false);
  const failed = result.evaluations.filter((e) => !e.passed);
  const passed = result.evaluations.filter((e) => e.passed);

  return (
    <div
      className={`bg-white border rounded p-5 ${
        result.eligible ? "border-green-300" : "border-slate-200"
      }`}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="font-semibold">{result.lender_name}</h3>
            {result.eligible ? (
              <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">
                eligible
              </span>
            ) : (
              <span className="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded">
                ineligible
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500">
            {result.program_name ?? "no matching program"}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold">
            {result.fit_score.toFixed(0)}
          </div>
          <div className="text-xs text-slate-500">fit score</div>
        </div>
      </div>

      {failed.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs uppercase text-slate-500 mb-1">Failed criteria</p>
          <ul className="space-y-1">
            {failed.map((e) => (
              <EvalRow key={e.id} ev={e} failed />
            ))}
          </ul>
        </div>
      ) : null}

      {result.evaluations.length > 0 ? (
        <button
          onClick={() => setOpen((o) => !o)}
          className="mt-3 text-xs text-blue-600 underline"
        >
          {open ? "Hide" : "Show"} all {result.evaluations.length} criteria
        </button>
      ) : null}

      {open ? (
        <div className="mt-3 space-y-1">
          <p className="text-xs uppercase text-slate-500">Passed criteria</p>
          <ul className="space-y-1">
            {passed.map((e) => (
              <EvalRow key={e.id} ev={e} />
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function EvalRow({ ev, failed }: { ev: RuleEvaluation; failed?: boolean }) {
  return (
    <li className="text-sm flex gap-2">
      <span className={failed ? "text-red-600" : "text-green-600"}>
        {failed ? "✗" : "✓"}
      </span>
      <span>{ev.message}</span>
    </li>
  );
}
