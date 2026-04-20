import Link from "next/link";

const items = [
  { href: "/", label: "Dashboard" },
  { href: "/corporate", label: "Corporate" },
  { href: "/properties", label: "Properties" },
  { href: "/tenants", label: "Tenants" },
  { href: "/vendors", label: "Vendors" },
  { href: "/renewals", label: "Renewals" },
  { href: "/communications", label: "Communications" },
  { href: "/policies/new", label: "+ New Policy" },
];

export default function Nav() {
  return (
    <header className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-8">
        <Link href="/" className="font-semibold text-slate-900">
          Rentor Insurance
        </Link>
        <nav className="flex items-center gap-5 text-sm">
          {items.map((i) => (
            <Link key={i.href} href={i.href} className="text-slate-600 hover:text-brand-600">
              {i.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
