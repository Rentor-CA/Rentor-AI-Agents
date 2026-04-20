import PolicyTable from "@/components/PolicyTable";
import { expiringSoon, listTemplates } from "@/lib/policies";

export const dynamic = "force-dynamic";

export default async function Renewals() {
  const [rows, templates] = await Promise.all([expiringSoon(180), listTemplates()]);
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Renewals</h1>
          <p className="text-slate-500">Policies expiring within 180 days or already lapsed.</p>
        </div>
        <form action="/api/renewals/run" method="post">
          <button className="bg-brand-600 text-white px-4 py-2 rounded-md text-sm hover:bg-brand-700">
            Scan & Queue Communications
          </button>
        </form>
      </div>

      <PolicyTable rows={rows} />

      <section>
        <h2 className="text-lg font-semibold mb-3">Communication Templates</h2>
        <div className="grid md:grid-cols-2 gap-3">
          {templates.map((t) => (
            <div key={t.key} className="bg-white border border-slate-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="font-medium">{t.name}</div>
                <span className="text-xs bg-slate-100 px-2 py-0.5 rounded">{t.days_before_expiration}d</span>
              </div>
              <div className="text-xs text-slate-500 mt-1 capitalize">{t.entity_type ?? "any"} · {t.key}</div>
              <div className="mt-2 text-sm font-medium">{t.subject}</div>
              <pre className="mt-1 text-xs text-slate-600 whitespace-pre-wrap">{t.body}</pre>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
