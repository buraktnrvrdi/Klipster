import type { MetadataRoute } from "next";

const SITE_URL = "https://klipster.com.tr";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/app", "/profil", "/email-dogrula", "/sifre-sifirla", "/sifremi-unuttum", "/davet", "/odeme"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
