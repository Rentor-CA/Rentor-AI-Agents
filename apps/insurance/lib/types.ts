export type EntityType = "corporate" | "property" | "tenant" | "vendor";

export type PolicyKind =
  | "protection_plus_bundle"
  | "scheer_landlord_protection"
  | "master_general_liability"
  | "master_tenant_liability"
  | "property_hazard"
  | "tenant_renters"
  | "vendor_general_liability"
  | "vendor_workers_comp"
  | "vendor_auto"
  | "corporate_eo"
  | "corporate_cyber"
  | "corporate_umbrella"
  | "other";

export type PolicyStatus = "active" | "pending" | "expired" | "cancelled" | "lapsed";

export interface InsurancePolicy {
  id: string;
  entity_type: EntityType;
  entity_ref_id: string | null;
  entity_name: string | null;
  policy_kind: PolicyKind;
  carrier: string | null;
  policy_number: string | null;
  coverage_amount: number | null;
  premium_amount: number | null;
  effective_date: string | null;
  expiration_date: string | null;
  status: PolicyStatus;
  auto_renew: boolean;
  document_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface InsurancePolicyEnriched extends InsurancePolicy {
  resolved_entity_name: string | null;
  days_until_expiration: number | null;
}

export interface RenewalTemplate {
  key: string;
  name: string;
  entity_type: EntityType | null;
  subject: string;
  body: string;
  days_before_expiration: number;
  created_at: string;
}

export interface Communication {
  id: string;
  policy_id: string | null;
  direction: "outbound" | "inbound";
  channel: "email" | "sms" | "phone" | "mail";
  recipient: string | null;
  subject: string | null;
  body: string | null;
  status: "queued" | "sent" | "delivered" | "failed" | "replied";
  scheduled_for: string | null;
  sent_at: string | null;
  template_key: string | null;
  created_at: string;
}

export const POLICY_KIND_LABELS: Record<PolicyKind, string> = {
  protection_plus_bundle: "Protection Plus Bundle (Landlord + GL)",
  scheer_landlord_protection: "Scheer Landlord Protection (Stand Alone)",
  master_general_liability: "Master General Liability ($1M)",
  master_tenant_liability: "Master Tenant Liability ($100K)",
  property_hazard: "Property Hazard / Owner Policy",
  tenant_renters: "Tenant Renters Insurance",
  vendor_general_liability: "Vendor General Liability",
  vendor_workers_comp: "Vendor Workers' Comp",
  vendor_auto: "Vendor Auto",
  corporate_eo: "Corporate E&O",
  corporate_cyber: "Corporate Cyber",
  corporate_umbrella: "Corporate Umbrella",
  other: "Other",
};

export const CORE_RENTOR_POLICIES: PolicyKind[] = [
  "protection_plus_bundle",
  "scheer_landlord_protection",
  "master_general_liability",
  "master_tenant_liability",
];
