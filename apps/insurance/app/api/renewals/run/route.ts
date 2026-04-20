import { NextResponse } from "next/server";
import { serviceClient } from "@/lib/supabase";
import { renderTemplate } from "@/lib/policies";
import type { RenewalTemplate, InsurancePolicyEnriched } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST() {
  const sb = serviceClient();

  const [{ data: templates }, { data: policies }] = await Promise.all([
    sb.from("insurance_renewal_templates").select("*"),
    sb.from("insurance_policies_enriched").select("*").not("expiration_date", "is", null),
  ]);

  const tmpls = (templates ?? []) as RenewalTemplate[];
  const pols = (policies ?? []) as InsurancePolicyEnriched[];
  const queued: any[] = [];

  for (const p of pols) {
    const days = p.days_until_expiration;
    if (days == null) continue;
    const candidate = tmpls
      .filter((t) => !t.entity_type || t.entity_type === p.entity_type)
      .find((t) => days <= t.days_before_expiration && days > t.days_before_expiration - 7);
    if (!candidate) continue;

    const { data: existing } = await sb
      .from("insurance_communications")
      .select("id")
      .eq("policy_id", p.id)
      .eq("template_key", candidate.key)
      .limit(1);
    if (existing && existing.length > 0) continue;

    const { data: contact } = await sb
      .from("insurance_contacts")
      .select("*")
      .eq("policy_id", p.id)
      .limit(1)
      .maybeSingle();

    const vars = {
      entity_name: p.resolved_entity_name || p.entity_name || "",
      contact_name: contact?.name || "there",
      policy_number: p.policy_number || "",
      carrier: p.carrier || "",
      expiration_date: p.expiration_date || "",
      policy_kind: p.policy_kind,
    };

    queued.push({
      policy_id: p.id,
      direction: "outbound",
      channel: "email",
      recipient: contact?.email || null,
      subject: renderTemplate(candidate.subject, vars),
      body: renderTemplate(candidate.body, vars),
      status: "queued",
      template_key: candidate.key,
      scheduled_for: new Date().toISOString(),
    });
  }

  if (queued.length > 0) {
    await sb.from("insurance_communications").insert(queued);
  }

  return NextResponse.redirect(new URL("/communications", process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3100"), { status: 303 });
}
