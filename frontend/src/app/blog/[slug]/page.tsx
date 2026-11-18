import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowRight } from "lucide-react";
import BlogShell from "@/components/BlogShell";
import { POSTS, getPost } from "@/lib/blog";

const SITE_URL = "https://klipster.com.tr";

export function generateStaticParams() {
  return POSTS.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) return {};
  return {
    title: post.title,
    description: post.description,
    alternates: { canonical: `/blog/${post.slug}` },
    openGraph: {
      type: "article",
      locale: "tr_TR",
      url: `${SITE_URL}/blog/${post.slug}`,
      siteName: "Klipster",
      title: post.title,
      description: post.description,
      publishedTime: post.date,
    },
  };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    description: post.description,
    datePublished: post.date,
    dateModified: post.date,
    inLanguage: "tr",
    mainEntityOfPage: `${SITE_URL}/blog/${post.slug}`,
    author: { "@type": "Organization", name: "Klipster" },
    publisher: { "@type": "Organization", name: "Klipster", logo: { "@type": "ImageObject", url: `${SITE_URL}/logo-v2.png` } },
  };

  return (
    <BlogShell backHref="/blog" backLabel="Rehberler">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <article>
        <p className="text-xs text-zinc-500">
          {new Date(post.date).toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })} ·{" "}
          {post.readMinutes} dk okuma
        </p>
        <h1 className="mt-3 font-display text-3xl sm:text-4xl font-semibold tracking-tight leading-tight">
          {post.title}
        </h1>

        <div className="mt-8 space-y-5">
          {post.blocks.map((b, i) => {
            if (b.type === "h2")
              return (
                <h2 key={i} className="pt-4 font-display text-xl font-semibold text-white">
                  {b.text}
                </h2>
              );
            if (b.type === "p")
              return (
                <p key={i} className="leading-relaxed text-zinc-300">
                  {b.text}
                </p>
              );
            const List = b.type === "ol" ? "ol" : "ul";
            return (
              <List
                key={i}
                className={`space-y-2 pl-5 text-zinc-300 leading-relaxed ${b.type === "ol" ? "list-decimal" : "list-disc"} marker:text-red-500`}
              >
                {b.items.map((it) => (
                  <li key={it}>{it}</li>
                ))}
              </List>
            );
          })}
        </div>
      </article>

      <div className="mt-14 rounded-2xl border border-red-500/20 bg-red-500/[0.06] p-6">
        <h2 className="font-display text-xl font-semibold">Videonu kliplere çevirmeyi dene</h2>
        <p className="mt-2 text-sm text-zinc-400">
          Videonu yükle ya da YouTube linkini yapıştır, dakikalar içinde altyazılı dikey klipler hazır olsun. Kredi kartı gerekmez.
        </p>
        <Link href="/kayit" className="noir-shiny-cta group mt-5 inline-flex">
          Ücretsiz Dene
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </BlogShell>
  );
}
