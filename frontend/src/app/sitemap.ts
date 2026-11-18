import type { MetadataRoute } from "next";
import { POSTS } from "@/lib/blog";

const SITE_URL = "https://klipster.com.tr";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE_URL}/blog`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    ...POSTS.map((p) => ({
      url: `${SITE_URL}/blog/${p.slug}`,
      lastModified: new Date(p.date),
      changeFrequency: "monthly" as const,
      priority: 0.7,
    })),
    { url: `${SITE_URL}/giris`, lastModified: now, changeFrequency: "monthly", priority: 0.3 },
    { url: `${SITE_URL}/kayit`, lastModified: now, changeFrequency: "monthly", priority: 0.5 },
    { url: `${SITE_URL}/iletisim`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE_URL}/gizlilik-politikasi`, lastModified: now, changeFrequency: "yearly", priority: 0.1 },
    { url: `${SITE_URL}/kullanim-kosullari`, lastModified: now, changeFrequency: "yearly", priority: 0.1 },
  ];
}
