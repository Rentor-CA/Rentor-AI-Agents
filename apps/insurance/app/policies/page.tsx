import PolicyTable from "@/components/PolicyTable";
import { listPolicies } from "@/lib/policies";

export const dynamic = "force-dynamic";

export default async function AllPolicies() {
  const rows = await listPolicies();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">All Policies</h1>
      <PolicyTable rows={rows} />
    </div>
  );
}
