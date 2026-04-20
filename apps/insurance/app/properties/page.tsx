import PolicyTable from "@/components/PolicyTable";
import { listPolicies } from "@/lib/policies";

export const dynamic = "force-dynamic";

export default async function Properties() {
  const rows = await listPolicies({ entity_type: "property" });
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Property Insurance</h1>
      <p className="text-slate-500">Owner policies pulled from the Rentor Vault (AppFolio sync) and linked to policy records.</p>
      <PolicyTable rows={rows} />
    </div>
  );
}
