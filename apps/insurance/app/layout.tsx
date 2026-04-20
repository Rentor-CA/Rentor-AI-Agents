import "./globals.css";
import Nav from "@/components/Nav";

export const metadata = { title: "Rentor Insurance Hub", description: "Track & renew insurance policies across Rentor." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
