import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Program, Rule } from "../types";

const KINDS = ["numeric", "set", "boolean", "composite"] as const;
const OPS_BY_KIND: Record<(typeof KINDS)[number], string[]> = {
  numeric: ["gte", "lte", "gt", "lt", "eq", "between"],
  set: ["in", "not_in"],
  boolean: ["eq"],
  composite: ["call"],
};

export default function LenderDetail() {
  const { id } = useParams();
  const lenderId = Number(id);
  const { data, isLoading } = useQuery({
    queryKey: ["lender", lenderId],
    queryFn: () => api.getLender(lenderId),
    enabled: !Number.isNaN(lenderId),
  });

  if (isLoading) return <p>Loading…</p>;
  if (!data) return <p>Lender not found</p>;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded p-5">
        <h2 className="text-lg font-semibold">{data.name}</h2>
        {data.contact ? (
          <p className="text-sm text-slate-500">{data.contact}</p>
        ) : null}
        {data.notes ? (
          <p className="text-sm text-slate-700 mt-2 whitespace-pre-line">{data.notes}</p>
        ) : null}
      </div>

      {data.programs.map((p) => (
        <ProgramCard key={p.id} program={p} lenderId={lenderId} />
      ))}
    </div>
  );
}

function ProgramCard({ program, lenderId }: { program: Program; lenderId: number }) {
  const [adding, setAdding] = useState(false);
  return (
    <div className="bg-white border border-slate-200 rounded p-5">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold">{program.name}</h3>
          {program.notes ? (
            <p className="text-sm text-slate-500">{program.notes}</p>
          ) : null}
        </div>
        {program.base_rate ? (
          <div className="text-sm text-slate-500">
            Base rate {program.base_rate.toFixed(2)}%
          </div>
        ) : null}
      </div>

      <div className="mt-4 space-y-2">
        {program.rules.map((r) => (
          <RuleRow key={r.id} rule={r} lenderId={lenderId} />
        ))}
      </div>

      <div className="mt-3">
        {adding ? (
          <NewRuleForm
            programId={program.id}
            lenderId={lenderId}
            onDone={() => setAdding(false)}
          />
        ) : (
          <button
            onClick={() => setAdding(true)}
            className="text-xs text-blue-600 underline"
          >
            + add rule
          </button>
        )}
      </div>
    </div>
  );
}

function NewRuleForm({
  programId,
  lenderId,
  onDone,
}: {
  programId: number;
  lenderId: number;
  onDone: () => void;
}) {
  const [kind, setKind] = useState<(typeof KINDS)[number]>("numeric");
  const [field, setField] = useState("guarantor.fico");
  const [op, setOp] = useState("gte");
  const [valueStr, setValueStr] = useState("700");
  const [weight, setWeight] = useState(3);
  const [hard, setHard] = useState(true);
  const [message, setMessage] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const qc = useQueryClient();

  const mut = useMutation({
    mutationFn: () => {
      let value: unknown;
      try {
        value = JSON.parse(valueStr);
      } catch {
        value = valueStr;
      }
      return api.addRule(programId, {
        kind,
        field,
        op,
        value,
        weight,
        hard,
        message: message || null,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lender", lenderId] });
      onDone();
    },
    onError: (e) => setErr((e as Error).message),
  });

  return (
    <div className="border border-slate-200 rounded p-3 bg-slate-50 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
      <label className="block">
        kind
        <select
          className="block w-full border border-slate-300 rounded px-2 py-1"
          value={kind}
          onChange={(e) => {
            const k = e.target.value as (typeof KINDS)[number];
            setKind(k);
            setOp(OPS_BY_KIND[k][0]);
          }}
        >
          {KINDS.map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
      </label>
      <label className="block">
        field
        <input
          className="block w-full border border-slate-300 rounded px-2 py-1"
          value={field}
          onChange={(e) => setField(e.target.value)}
        />
      </label>
      <label className="block">
        op
        <select
          className="block w-full border border-slate-300 rounded px-2 py-1"
          value={op}
          onChange={(e) => setOp(e.target.value)}
        >
          {OPS_BY_KIND[kind].map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>
      </label>
      <label className="block">
        value (JSON)
        <input
          className="block w-full border border-slate-300 rounded px-2 py-1 font-mono"
          value={valueStr}
          onChange={(e) => setValueStr(e.target.value)}
        />
      </label>
      <label className="block">
        weight
        <input
          type="number"
          className="block w-full border border-slate-300 rounded px-2 py-1"
          value={weight}
          onChange={(e) => setWeight(Number(e.target.value))}
        />
      </label>
      <label className="flex items-center gap-2 mt-4">
        <input
          type="checkbox"
          checked={hard}
          onChange={(e) => setHard(e.target.checked)}
        />
        hard
      </label>
      <label className="block col-span-2">
        message (optional)
        <input
          className="block w-full border border-slate-300 rounded px-2 py-1"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="FICO {actual} below required {required}"
        />
      </label>
      <div className="col-span-2 md:col-span-4 flex gap-2 mt-1">
        <button
          onClick={() => mut.mutate()}
          disabled={mut.isPending}
          className="bg-slate-900 text-white px-3 py-1 rounded text-xs"
        >
          {mut.isPending ? "Saving…" : "Save rule"}
        </button>
        <button onClick={onDone} className="text-slate-500 text-xs">
          Cancel
        </button>
        {err ? <span className="text-red-600 ml-2">{err}</span> : null}
      </div>
    </div>
  );
}

function RuleRow({ rule, lenderId }: { rule: Rule; lenderId: number }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(JSON.stringify(rule.value));
  const [weight, setWeight] = useState(rule.weight);
  const [hard, setHard] = useState(rule.hard);
  const qc = useQueryClient();

  const update = useMutation({
    mutationFn: () =>
      api.updateRule(rule.id, {
        kind: rule.kind,
        field: rule.field,
        op: rule.op,
        value: JSON.parse(value),
        weight,
        hard,
        message: rule.message,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lender", lenderId] });
      setEditing(false);
    },
  });

  const remove = useMutation({
    mutationFn: () => api.deleteRule(rule.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lender", lenderId] }),
  });

  return (
    <div className="border border-slate-100 rounded p-3 text-sm">
      <div className="flex justify-between items-start gap-4">
        <div className="font-mono text-xs">
          <span className="text-slate-500">{rule.kind}</span>{" "}
          <span className="font-semibold">{rule.field}</span>{" "}
          <span className="text-slate-500">{rule.op}</span>{" "}
          {editing ? (
            <input
              className="border border-slate-300 rounded px-2 py-1 text-xs w-72"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          ) : (
            <span>{JSON.stringify(rule.value)}</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs">
          {editing ? (
            <>
              <label className="flex items-center gap-1">
                w
                <input
                  type="number"
                  className="border border-slate-300 rounded w-14 px-2 py-1"
                  value={weight}
                  onChange={(e) => setWeight(Number(e.target.value))}
                />
              </label>
              <label className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={hard}
                  onChange={(e) => setHard(e.target.checked)}
                />
                hard
              </label>
              <button
                onClick={() => update.mutate()}
                className="bg-slate-900 text-white px-3 py-1 rounded"
                disabled={update.isPending}
              >
                Save
              </button>
              <button onClick={() => setEditing(false)} className="text-slate-500">
                Cancel
              </button>
            </>
          ) : (
            <>
              <span className="text-slate-500">
                weight {rule.weight} · {rule.hard ? "hard" : "soft"}
              </span>
              <button
                onClick={() => setEditing(true)}
                className="text-blue-600 underline"
              >
                edit
              </button>
              <button
                onClick={() => {
                  if (confirm("Delete this rule?")) remove.mutate();
                }}
                className="text-red-600 underline"
              >
                delete
              </button>
            </>
          )}
        </div>
      </div>
      {rule.message ? (
        <p className="text-slate-500 mt-1">{rule.message}</p>
      ) : null}
    </div>
  );
}
