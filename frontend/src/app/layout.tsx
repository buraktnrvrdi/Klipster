import type { Metadata } from "next";
import { Geist, Geist_Mono, Sora } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: "500",
});

const SITE_URL = "https://klipster.com.tr";
const TITLE = "Klipster — Videolarını Viral Kliplere Dönüştür";
const DESCRIPTION =
  "Yapay zeka ile uzun videolarını (podcast, röportaj, canlı yayın) altyazılı, dikey (9:16) kısa kliplere dönüştür. TikTok, Instagram Reels ve YouTube Shorts için hazır.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE,
    template: "%s | Klipster",
  },
  description: DESCRIPTION,
  keywords: [
    "klip üretici", "video klip", "viral klip", "TikTok klip", "Instagram Reels",
    "YouTube Shorts", "yapay zeka video düzenleme", "altyazı ekleme", "dikey video",
  ],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "tr_TR",
    url: SITE_URL,
    siteName: "Klipster",
    title: TITLE,
    description: DESCRIPTION,
    images: [{ url: "/logo-v2.png", width: 673, height: 627, alt: "Klipster" }],
  },
  twitter: {
    card: "summary",
    title: TITLE,
    description: DESCRIPTION,
    images: ["/logo-v2.png"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} ${sora.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
