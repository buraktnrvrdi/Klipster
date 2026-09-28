"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

export default function OdemeSonucPage() {
  return (
    <Suspense fallback={null}>
      <OdemeSonucContent />
    </Suspense>
  );
}

function OdemeSonucContent() {
  const searchParams = useSearchParams();
  const basarili = searchParams.get("durum") === "basarili";

  return (
    <main className="noir-selection relative min-h-screen bg-black text-white flex items-center justify-center px-6 overflow-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0202] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-red-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="relative z-10 w-full max-w-sm text-center">
        <Link href="/" className="flex items-center justify-center mb-6">
          <Logo className="h-20" />
        </Link>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl">
          {basarili ? (
            <>
              <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h1 className="text-xl font-semibold font-display">Ödeme başarılı</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Aboneliğin aktif edildi. Yeni plan haklarını hemen kullanmaya başlayabilirsin.
              </p>
              <Link
                href="/app"
                className="mt-6 inline-block bg-red-500 hover:bg-red-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition"
              >
                Uygulamaya git
              </Link>
            </>
          ) : (
            <>
              <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h1 className="text-xl font-semibold font-display">Ödeme tamamlanamadı</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Kartından çekim yapılmadı. Tekrar denemek ister misin?
              </p>
              <Link
                href="/profil"
                className="mt-6 inline-block bg-white/5 hover:bg-white/10 border border-white/10 text-white px-6 py-2.5 rounded-full font-semibold text-sm transition"
              >
                Profile dön
              </Link>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
