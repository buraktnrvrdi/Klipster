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
    "klip üretici", "klip oluşturucu", "video klip", "viral klip", "TikTok klip", "Instagram Reels",
    "YouTube Shorts", "shorts oluşturucu", "yapay zeka video düzenleme", "altyazı ekleme",
    "otomatik altyazı ekleme", "dikey video", "viral video nasıl yapılır",
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

const ORGANIZATION_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Klipster",
  url: SITE_URL,
  logo: `${SITE_URL}/logo-v2.png`,
  description: DESCRIPTION,
  sameAs: [
    "https://www.instagram.com/klipster.tr",
    "https://x.com/klipstertr",
    "https://www.tiktok.com/@klipster.tr",
  ],
};

const WEBSITE_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Klipster",
  url: SITE_URL,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} ${sora.variable} h-full antialiased`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(ORGANIZATION_JSON_LD) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(WEBSITE_JSON_LD) }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
