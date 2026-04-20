import Link from "next/link";
import { expiringSoon, listPolicies } from "@/lib/policies";
import PolicyTable from "@/components/PolicyTable";
import { CORE_RENTOR_POLICIES, POLICY_KIND_LABELS } from "@/lib/types";

export const dynamic = "force-dynamic";

function Stat({ label, value, href }: { label: string; value: number | string; href?: string }) {
  const inner = (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-3xl font-semibold">{value}</div>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

export default async function Dashboard() {
  const [all, expiring] = await Promise.all([listPolicies(), expiringSoon(90)]);
  const counts = {
    total: all.length,
    corporate: all.filter((p) => p.entity_type === "corporate").length,
    property: all.filter((p) => p.entity_type === "property").length,
    tenant: all.filter((p) => p.entity_type === "tenant").length,
    vendor: all.filter((p) => p.entity_type === "vendor").length,
    expired: all.filter((p) => (p.days_until_expiration ?? 1) < 0).length,
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Insurance Hub</h1>
          <p className="text-slate-500">Corporate, property, tenant, and vendor coverage at a glance.</p>
        </div>
        <form action="/api/renewals/run" method="post">
          <button className="bg-brand-600 text-white px-4 py-2 rounded-md text-sm hover:bg-brand-700">
            Scan & Queue Renewals
          </button>
        </form>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Stat label="Total Policies" value={counts.total} href="/policies" />
        <Stat label="Corporate" value={counts.corporate} href="/corporate" />
        <Stat label="Properties" value={counts.property} href="/properties" />
        <Stat label="Tenants" value={counts.tenant} href="/tenants" />
        <Stat label="Vendors" value={counts.vendor} href="/vendors" />
        <Stat label="Expired" value={counts.expired} href="/renewals" />
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Core Rentor Policies</h2>
        <div className="grid md:grid-cols-2 gap-3">
          {CORE_RENTOR_POLICIES.map((k) => {
            const match = all.find((p) => p.policy_kind === k);
            return (
              <div key={k} className="bg-white rounded-lg border border-slate-200 p-4">
                <div className="font-medium">{POLICY_KIND_LABELS[k]}</div>
                <div className="mt-2 text-sm text-slate-600">
                  {match ? (
                    <>
                      {match.carrier || "—"} · Expires {match.expiration_date || "—"} ·{" "}
                      {match.days_until_expiration != null ? `${match.days_until_expiration}d` : "—"}
                    </>
                  ) : (
                    <Link href={`/policies/new?policy_kind=${k}&entity_type=corporate`} className="text-brand-600 underline">
                      Add policy
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Expiring in next 90 days</h2>
          <Link href="/renewals" className="text-sm text-brand-600">View all →</Link>
        </div>
        <PolicyTable rows={expiring} />
      </section>
    </div>
  );
}
