"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { browserClient } from "@/lib/supabase";
import { POLICY_KIND_LABELS, type EntityType, type PolicyKind } from "@/lib/types";

const ENTITY_TYPES: EntityType[] = ["corporate", "property", "tenant", "vendor"];

export default function NewPolicy() {
  const router = useRouter();
  const sp = useSearchParams();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    entity_type: (sp.get("entity_type") as EntityType) || "corporate",
    entity_ref_id: "",
    entity_name: "",
    policy_kind: (sp.get("policy_kind") as PolicyKind) || "other",
    carrier: "",
    policy_number: "",
    coverage_amount: "",
    premium_amount: "",
    effective_date: "",
    expiration_date: "",
    auto_renew: false,
    document_url: "",
    notes: "",
  });

  function set<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      ...form,
      coverage_amount: form.coverage_amount ? Number(form.coverage_amount) : null,
      premium_amount: form.premium_amount ? Number(form.premium_amount) : null,
      effective_date: form.effective_date || null,
      expiration_date: form.expiration_date || null,
    };
    const sb = browserClient();
    const { error } = await sb.from("insurance_policies").insert(payload);
    setSaving(false);
    if (error) {
      setError(error.message);
      return;
    }
    router.push(redirectFor(form.entity_type));
    router.refresh();
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">New Insurance Policy</h1>
      <form onSubmit={submit} className="space-y-4 bg-white rounded-lg border border-slate-200 p-6">
        <Row label="Entity Type">
          <select className="input" value={form.entity_type} onChange={(e) => set("entity_type", e.target.value as EntityType)}>
            {ENTITY_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </Row>
        <Row label="Entity Reference ID" hint="AppFolio property/tenant/vendor ID (leave blank for corporate).">
          <input className="input" value={form.entity_ref_id} onChange={(e) => set("entity_ref_id", e.target.value)} />
        </Row>
        <Row label="Entity Name">
          <input className="input" value={form.entity_name} onChange={(e) => set("entity_name", e.target.value)} />
        </Row>
        <Row label="Policy Kind">
          <select className="input" value={form.policy_kind} onChange={(e) => set("policy_kind", e.target.value as PolicyKind)}>
            {Object.entries(POLICY_KIND_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Row>
        <div className="grid grid-cols-2 gap-4">
          <Row label="Carrier"><input className="input" value={form.carrier} onChange={(e) => set("carrier", e.target.value)} /></Row>
          <Row label="Policy #"><input className="input" value={form.policy_number} onChange={(e) => set("policy_number", e.target.value)} /></Row>
          <Row label="Coverage $"><input className="input" type="number" value={form.coverage_amount} onChange={(e) => set("coverage_amount", e.target.value)} /></Row>
          <Row label="Premium $"><input className="input" type="number" value={form.premium_amount} onChange={(e) => set("premium_amount", e.target.value)} /></Row>
          <Row label="Effective"><input className="input" type="date" value={form.effective_date} onChange={(e) => set("effective_date", e.target.value)} /></Row>
          <Row label="Expiration"><input className="input" type="date" value={form.expiration_date} onChange={(e) => set("expiration_date", e.target.value)} /></Row>
        </div>
        <Row label="Document URL"><input className="input" value={form.document_url} onChange={(e) => set("document_url", e.target.value)} /></Row>
        <Row label="Notes"><textarea className="input" rows={3} value={form.notes} onChange={(e) => set("notes", e.target.value)} /></Row>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.auto_renew} onChange={(e) => set("auto_renew", e.target.checked)} />
          Auto-renew
        </label>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <button disabled={saving} className="bg-brand-600 text-white px-4 py-2 rounded-md text-sm hover:bg-brand-700 disabled:opacity-50">
          {saving ? "Saving…" : "Save Policy"}
        </button>
      </form>
      <style jsx global>{`
        .input { @apply block w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500; }
      `}</style>
    </div>
  );
}

function Row({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      {children}
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  );
}

function redirectFor(t: EntityType) {
  return t === "corporate" ? "/corporate" : `/${t === "property" ? "properties" : t + "s"}`;
}
