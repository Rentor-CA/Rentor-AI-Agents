// Standalone cron entrypoint: `npm run renewals:scan`
// Intended to be scheduled daily (e.g. via Supabase cron or GitHub Actions).

import "dotenv/config";

async function main() {
  const base = process.env.INSURANCE_APP_URL || "http://localhost:3100";
  const scan = await fetch(`${base}/api/renewals/run`, { method: "POST", redirect: "manual" });
  console.log("renewals scan:", scan.status);
  const send = await fetch(`${base}/api/communications/send`, { method: "POST" });
  console.log("send:", send.status, await send.text());
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
