import Link from "next/link";
import { POLICY_KIND_LABELS, type InsurancePolicyEnriched } from "@/lib/types";

function fmtDate(d?: string | null) {
  return d ? new Date(d).toLocaleDateString() : "—";
}

function fmtMoney(n?: number | null) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

function badge(days: number | null | undefined) {
  if (days == null) return <span className="text-slate-400">—</span>;
  if (days < 0) return <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs">Expired {Math.abs(days)}d</span>;
  if (days <= 30) return <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs">{days}d left</span>;
  if (days <= 60) return <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 text-xs">{days}d left</span>;
  if (days <= 90) return <span className="px-2 py-0.5 rounded bg-yellow-100 text-yellow-700 text-xs">{days}d left</span>;
  return <span className="text-slate-500 text-xs">{days}d left</span>;
}

export default function PolicyTable({ rows }: { rows: InsurancePolicyEnriched[] }) {
  if (rows.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-500">
        No policies yet. <Link className="text-brand-600 underline" href="/policies/new">Add one</Link>.
      </div>
    );
  }
  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Entity</th>
            <th className="text-left px-4 py-2 font-medium">Policy</th>
            <th className="text-left px-4 py-2 font-medium">Carrier</th>
            <th className="text-left px-4 py-2 font-medium">Coverage</th>
            <th className="text-left px-4 py-2 font-medium">Expires</th>
            <th className="text-left px-4 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-slate-100">
              <td className="px-4 py-2">
                <div className="font-medium">{r.resolved_entity_name || r.entity_name || "—"}</div>
                <div className="text-xs text-slate-500 capitalize">{r.entity_type}</div>
              </td>
              <td className="px-4 py-2">
                <div>{POLICY_KIND_LABELS[r.policy_kind]}</div>
                <div className="text-xs text-slate-500">{r.policy_number || "—"}</div>
              </td>
              <td className="px-4 py-2">{r.carrier || "—"}</td>
              <td className="px-4 py-2">{fmtMoney(r.coverage_amount)}</td>
              <td className="px-4 py-2">
                <div>{fmtDate(r.expiration_date)}</div>
                <div>{badge(r.days_until_expiration)}</div>
              </td>
              <td className="px-4 py-2 capitalize">{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
