# Rentor Insurance Hub

Centralized tracking for every insurance policy that touches Rentor — corporate master policies, property owner coverage pulled from the Rentor Vault (Supabase/AppFolio sync), tenant renters insurance, and vendor COIs — plus an automated renewal communication system.

## What it tracks

**Corporate policies** (first-class):
- **Protection Plus Bundle** — Landlord Protection + General Liability
- **Scheer Landlord Protection (Stand Alone)** — Loss of rent, eviction costs, malicious damage
- **Master General Liability (Stand Alone)** — $1M general liability
- **Master Tenant Liability** — $100K tenant-caused damage (fire/smoke/water)
- E&O, cyber, umbrella, and any other Rentor corporate policy

**Property insurance** — auto-joined against `appfolio_properties` in the Rentor Vault.

**Tenant insurance** — renters COIs linked to `appfolio_tenants`.

**Vendor insurance** — GL / workers' comp / auto COIs linked to `appfolio_vendors`.

## Renewal automation

1. Cron (or the "Scan & Queue Renewals" button on the dashboard) hits `/api/renewals/run`.
2. The scanner compares each policy's `days_until_expiration` against the matching template's `days_before_expiration` and queues a row in `insurance_communications` (idempotent per `(policy_id, template_key)`).
3. `/api/communications/send` drains the queue via Resend and logs delivery.
4. `scripts/scan-renewals.ts` chains both endpoints for a single cron invocation.

Templates live in `insurance_renewal_templates` and support `{{entity_name}}`, `{{contact_name}}`, `{{policy_number}}`, `{{carrier}}`, `{{expiration_date}}`, `{{policy_kind}}` variables.

## Stack

Next.js 15 (App Router) · TypeScript · Tailwind · Supabase (`opdnbjdhvxxayeomvufg` / RentorOS).

## Setup

```bash
cd apps/insurance
cp .env.local.example .env.local   # fill SUPABASE_SERVICE_ROLE_KEY and RESEND_API_KEY
npm install
npm run dev                        # http://localhost:3100
```

Schema is already applied via Supabase migration `create_insurance_hub_tables`.
