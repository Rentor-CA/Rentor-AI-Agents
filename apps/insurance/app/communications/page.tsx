import { serverClient } from "@/lib/supabase";
import type { Communication } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Communications() {
  const sb = await serverClient();
  const { data } = await sb.from("insurance_communications").select("*").order("created_at", { ascending: false }).limit(200);
  const rows = (data ?? []) as Communication[];
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Communications Log</h1>
      <p className="text-slate-500">Every renewal reminder sent or queued by the hub.</p>
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left px-4 py-2 font-medium">When</th>
              <th className="text-left px-4 py-2 font-medium">Channel</th>
              <th className="text-left px-4 py-2 font-medium">Recipient</th>
              <th className="text-left px-4 py-2 font-medium">Subject</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-4 py-2">{new Date(r.created_at).toLocaleString()}</td>
                <td className="px-4 py-2 capitalize">{r.channel}</td>
                <td className="px-4 py-2">{r.recipient || "—"}</td>
                <td className="px-4 py-2">{r.subject || "—"}</td>
                <td className="px-4 py-2 capitalize">{r.status}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">No communications yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
