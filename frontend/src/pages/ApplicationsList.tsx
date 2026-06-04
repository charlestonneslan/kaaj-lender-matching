import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function ApplicationsList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["applications"],
    queryFn: api.listApplications,
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-600">Failed to load applications</p>;

  if (!data || data.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded p-8 text-center">
        <p className="text-slate-600 mb-4">No applications yet.</p>
        <Link
          to="/new"
          className="inline-block bg-slate-900 text-white px-4 py-2 rounded text-sm"
        >
          Create your first application
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="px-4 py-2">#</th>
            <th className="px-4 py-2">Business</th>
            <th className="px-4 py-2">Industry</th>
            <th className="px-4 py-2">State</th>
            <th className="px-4 py-2">Amount</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Created</th>
          </tr>
        </thead>
        <tbody>
          {data.map((a) => (
            <tr key={a.id} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-4 py-2">
                <Link to={`/applications/${a.id}`} className="text-blue-600 underline">
                  {a.id}
                </Link>
              </td>
              <td className="px-4 py-2">{a.legal_name ?? "?"}</td>
              <td className="px-4 py-2">{a.industry ?? "?"}</td>
              <td className="px-4 py-2">{a.state ?? "?"}</td>
              <td className="px-4 py-2">
                {a.amount ? `$${a.amount.toLocaleString()}` : "?"}
              </td>
              <td className="px-4 py-2">
                <StatusBadge status={a.status} />
              </td>
              <td className="px-4 py-2 text-slate-500">
                {new Date(a.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls = {
    draft: "bg-slate-200 text-slate-700",
    submitted: "bg-blue-100 text-blue-800",
    evaluated: "bg-green-100 text-green-800",
  }[status] ?? "bg-slate-200";
  return <span className={`px-2 py-0.5 rounded text-xs ${cls}`}>{status}</span>;
}
