import PolicyTable from "@/components/PolicyTable";
import { listPolicies } from "@/lib/policies";

export const dynamic = "force-dynamic";

export default async function Vendors() {
  const rows = await listPolicies({ entity_type: "vendor" });
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Vendor Insurance</h1>
      <p className="text-slate-500">Certificates of Insurance from approved vendors. Auto-reminders fire 30 days before expiration.</p>
      <PolicyTable rows={rows} />
    </div>
  );
}
