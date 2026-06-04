import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function LendersList() {
  const { data, isLoading } = useQuery({ queryKey: ["lenders"], queryFn: api.listLenders });

  if (isLoading) return <p>Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Link
          to="/lenders/new"
          className="bg-slate-900 text-white px-3 py-2 rounded text-sm"
        >
          + Add lender
        </Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(data ?? []).map((l) => (
          <Link
            key={l.id}
            to={`/lenders/${l.id}`}
            className="bg-white border border-slate-200 rounded p-5 hover:border-slate-400"
          >
            <h2 className="font-semibold">{l.name}</h2>
            <p className="text-sm text-slate-500 mt-1">
              {l.programs.length} program{l.programs.length === 1 ? "" : "s"} ·{" "}
              {l.contact ?? "no contact"}
            </p>
            {l.notes ? (
              <p className="text-sm text-slate-600 mt-2 line-clamp-3">{l.notes}</p>
            ) : null}
          </Link>
        ))}
      </div>
    </div>
  );
}
