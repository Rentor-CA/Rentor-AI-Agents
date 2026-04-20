import PolicyTable from "@/components/PolicyTable";
import { listPolicies } from "@/lib/policies";

export const dynamic = "force-dynamic";

export default async function Corporate() {
  const rows = await listPolicies({ entity_type: "corporate" });
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Corporate Policies</h1>
      <p className="text-slate-500">Rentor's master policies, E&O, cyber, umbrella, and the four core landlord/tenant programs.</p>
      <PolicyTable rows={rows} />
    </div>
  );
}
