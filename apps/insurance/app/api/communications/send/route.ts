import { NextResponse } from "next/server";
import { serviceClient } from "@/lib/supabase";

export const dynamic = "force-dynamic";

// Process the queue: for each queued communication with a recipient, send via Resend and mark sent.
export async function POST() {
  const sb = serviceClient();
  const resendKey = process.env.RESEND_API_KEY;
  const from = process.env.INSURANCE_FROM_EMAIL || "insurance@rentor.com";

  const { data: queued } = await sb
    .from("insurance_communications")
    .select("*")
    .eq("status", "queued")
    .eq("channel", "email")
    .limit(50);

  const results: { id: string; status: string; error?: string }[] = [];

  for (const c of queued ?? []) {
    if (!c.recipient) {
      await sb.from("insurance_communications").update({ status: "failed" }).eq("id", c.id);
      results.push({ id: c.id, status: "failed", error: "no recipient" });
      continue;
    }
    if (!resendKey) {
      results.push({ id: c.id, status: "skipped", error: "RESEND_API_KEY missing" });
      continue;
    }
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${resendKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from, to: [c.recipient], subject: c.subject, text: c.body }),
    });
    if (r.ok) {
      await sb.from("insurance_communications").update({ status: "sent", sent_at: new Date().toISOString() }).eq("id", c.id);
      results.push({ id: c.id, status: "sent" });
    } else {
      const err = await r.text();
      await sb.from("insurance_communications").update({ status: "failed" }).eq("id", c.id);
      results.push({ id: c.id, status: "failed", error: err.slice(0, 200) });
    }
  }

  return NextResponse.json({ processed: results.length, results });
}
