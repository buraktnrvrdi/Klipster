"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function GirisPage() {
  return (
    <Suspense fallback={null}>
      <GirisForm />
    </Suspense>
  );
}

function GirisForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [resent, setResent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setNeedsVerification(false);
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Giriş başarısız");
        if (res.status === 403) setNeedsVerification(true);
        return;
      }
      localStorage.setItem("klipster_token", data.token);
      router.push(inviteToken ? `/davet?token=${inviteToken}` : "/app");
    } catch {
      setError("Sunucuya ulaşılamadı, backend çalışıyor mu kontrol et");
    } finally {
      setLoading(false);
    }
  }

  async function handleResendVerification() {
    try {
      await fetch(`${API_URL}/api/auth/resend-verification-public`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setResent(true);
    } catch {
      // sessizce yoksay
    }
  }

  return (
    <main className="noir-selection relative min-h-screen bg-black text-white flex items-center justify-center px-6 overflow-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0d02] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-orange-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        <Link href="/" className="flex items-center gap-2 w-fit">
          <Logo className="h-9" />
        </Link>

        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl">
          <h1 className="text-2xl font-semibold font-display tracking-tight">Tekrar hoş geldin</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Hesabın yok mu?{" "}
            <Link
              href={inviteToken ? `/kayit?invite=${inviteToken}` : "/kayit"}
              className="text-orange-500 font-medium hover:underline"
            >
              Hemen oluştur
            </Link>
          </p>

          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
            <label className="text-sm">
              <span className="block mb-1.5 text-zinc-400 font-medium">E-posta</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-orange-500/60 transition-colors"
                placeholder="ornek@mail.com"
              />
            </label>
            <label className="text-sm">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-zinc-400 font-medium">Şifre</span>
                <Link href="/sifremi-unuttum" className="text-xs text-orange-500 hover:underline">
                  Şifremi unuttum
                </Link>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-orange-500/60 transition-colors"
                placeholder="••••••••"
              />
            </label>

            {error && (
              <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                <p>{error}</p>
                {needsVerification && (
                  <button
                    type="button"
                    onClick={handleResendVerification}
                    className="mt-1.5 text-xs font-semibold text-orange-400 hover:text-orange-300 transition-colors"
                  >
                    {resent ? "Gönderildi ✓" : "Doğrulama e-postasını tekrar gönder"}
                  </button>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 bg-orange-500 hover:bg-orange-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
            >
              {loading ? "Giriş yapılıyor..." : "Giriş yap"}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
