import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

export default function BlogShell({
  children,
  backHref = "/",
  backLabel = "Ana sayfa",
}: {
  children: React.ReactNode;
  backHref?: string;
  backLabel?: string;
}) {
  return (
    <main className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#160202] to-black" />
        <ParallaxStars speed={0.4} />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Logo className="h-14" />
          </Link>
          <Link
            href={backHref}
            className="flex items-center gap-1.5 text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {backLabel}
          </Link>
        </div>
      </header>

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-16">{children}</div>
    </main>
  );
}
