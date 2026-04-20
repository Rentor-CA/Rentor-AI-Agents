import PolicyTable from "@/components/PolicyTable";
import { listPolicies } from "@/lib/policies";

export const dynamic = "force-dynamic";

export default async function Tenants() {
  const rows = await listPolicies({ entity_type: "tenant" });
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Tenant Insurance</h1>
      <p className="text-slate-500">Renters insurance tracked from Rentor Vault. Master Tenant Liability covers gaps at $100K per occurrence.</p>
      <PolicyTable rows={rows} />
    </div>
  );
}
