import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import BlogShell from "@/components/BlogShell";
import { POSTS } from "@/lib/blog";

export const metadata: Metadata = {
  title: "Rehberler",
  description:
    "Uzun videolardan kısa klip çıkarma, otomatik altyazı ekleme ve YouTube Shorts üretimi hakkında Klipster rehberleri.",
  alternates: { canonical: "/blog" },
};

export default function BlogIndexPage() {
  return (
    <BlogShell>
      <h1 className="font-display text-3xl font-semibold tracking-tight">Rehberler</h1>
      <p className="mt-2 text-sm text-zinc-400">
        Uzun videolarından kısa, izlenen klipler çıkarmak için pratik yazılar.
      </p>

      <div className="mt-10 flex flex-col gap-4">
        {POSTS.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="group rounded-2xl border border-white/10 bg-white/[0.03] p-6 hover:border-red-500/40 transition-colors"
          >
            <p className="text-xs text-zinc-500">
              {new Date(post.date).toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })} ·{" "}
              {post.readMinutes} dk okuma
            </p>
            <h2 className="mt-2 font-display text-xl font-semibold text-white group-hover:text-red-400 transition-colors">
              {post.title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">{post.description}</p>
            <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-red-400">
              Oku <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>
        ))}
      </div>
    </BlogShell>
  );
}
