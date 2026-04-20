import { serverClient } from "./supabase";
import type { EntityType, InsurancePolicyEnriched, RenewalTemplate } from "./types";

export async function listPolicies(filter?: { entity_type?: EntityType }) {
  const sb = await serverClient();
  let q = sb.from("insurance_policies_enriched").select("*").order("expiration_date", { ascending: true });
  if (filter?.entity_type) q = q.eq("entity_type", filter.entity_type);
  const { data, error } = await q;
  if (error) throw error;
  return (data ?? []) as InsurancePolicyEnriched[];
}

export async function expiringSoon(days = 90) {
  const sb = await serverClient();
  const { data, error } = await sb
    .from("insurance_policies_enriched")
    .select("*")
    .lte("days_until_expiration", days)
    .gte("days_until_expiration", -30)
    .order("days_until_expiration", { ascending: true });
  if (error) throw error;
  return (data ?? []) as InsurancePolicyEnriched[];
}

export async function listTemplates() {
  const sb = await serverClient();
  const { data, error } = await sb.from("insurance_renewal_templates").select("*").order("days_before_expiration");
  if (error) throw error;
  return (data ?? []) as RenewalTemplate[];
}

export function renderTemplate(tpl: string, vars: Record<string, string | null | undefined>): string {
  return tpl.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, key) => (vars[key] ?? "").toString());
}
