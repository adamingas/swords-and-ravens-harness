import type { Metadata } from "next";
import { Cormorant_Garamond, IBM_Plex_Mono, Inter } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";

const sans = Inter({ variable: "--font-sans", subsets: ["latin"] });
const display = Cormorant_Garamond({ variable: "--font-display", subsets: ["latin"], weight: ["500", "600", "700"] });
const mono = IBM_Plex_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "500", "600"] });

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3000";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const imageUrl = `${protocol}://${host}/og.png`;
  return {
    title: "Raven Wire — Swords & Ravens WebSocket Explorer",
    description: "An interactive, data-backed guide to the Swords & Ravens game server protocol, from authentication to combat and game end.",
    icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
    openGraph: { title: "Raven Wire", description: "Inside the Swords & Ravens WebSocket Protocol", images: [{ url: imageUrl, width: 1733, height: 908 }] },
    twitter: { card: "summary_large_image", title: "Raven Wire", description: "Inside the Swords & Ravens WebSocket Protocol", images: [imageUrl] }
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${sans.variable} ${display.variable} ${mono.variable}`}>{children}</body></html>;
}
