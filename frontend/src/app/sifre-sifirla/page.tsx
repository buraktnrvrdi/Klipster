"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SifreSifirlaPage() {
  return (
    <Suspense fallback={null}>
      <SifreSifirlaForm />
    </Suspense>
  );
}

function SifreSifirlaForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) {
      setError("Bağlantı geçersiz - token eksik");
      return;
    }
    if (password.length < 6) {
      setError("Şifre en az 6 karakter olmalı");
      return;
    }
    if (password !== confirm) {
      setError("Şifreler eşleşmiyor");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail || "Şifre sıfırlanamadı");
        return;
      }
      setDone(true);
    } catch {
      setError("Sunucuya ulaşılamadı, backend çalışıyor mu kontrol et");
    } finally {
      setLoading(false);
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
          <Logo className="h-5" />
        </Link>

        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl">
          {!token ? (
            <>
              <div className="h-12 w-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <XCircle className="h-5 w-5 text-red-400" />
              </div>
              <h1 className="mt-4 text-xl font-semibold font-display tracking-tight">Bağlantı geçersiz</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Bu sayfaya doğrudan gelinmez - e-postandaki sıfırlama linkine tıklaman gerekir.
              </p>
              <Link
                href="/sifremi-unuttum"
                className="mt-6 inline-block bg-white/10 hover:bg-white/15 text-white px-5 py-2.5 rounded-full text-sm font-semibold transition"
              >
                Yeni link talep et
              </Link>
            </>
          ) : done ? (
            <>
              <div className="h-12 w-12 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <h1 className="mt-4 text-xl font-semibold font-display tracking-tight">Şifren değişti</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Artık yeni şifrenle giriş yapabilirsin. Güvenlik için önceki tüm oturumların kapatıldı.
              </p>
              <button
                onClick={() => router.push("/giris")}
                className="mt-6 bg-orange-500 hover:bg-orange-600 text-black px-5 py-2.5 rounded-full text-sm font-semibold transition"
              >
                Giriş yap
              </button>
            </>
          ) : (
            <>
              <h1 className="text-2xl font-semibold font-display tracking-tight">Yeni şifre belirle</h1>
              <p className="mt-2 text-sm text-zinc-400">Hesabın için yeni bir şifre gir.</p>

              <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
                <label className="text-sm">
                  <span className="block mb-1.5 text-zinc-400 font-medium">Yeni şifre</span>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-orange-500/60 transition-colors"
                    placeholder="En az 6 karakter"
                  />
                </label>
                <label className="text-sm">
                  <span className="block mb-1.5 text-zinc-400 font-medium">Yeni şifre (tekrar)</span>
                  <input
                    type="password"
                    required
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-orange-500/60 transition-colors"
                    placeholder="••••••••"
                  />
                </label>

                {error && (
                  <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    {error}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="mt-2 bg-orange-500 hover:bg-orange-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
                >
                  {loading ? "Kaydediliyor..." : "Şifreyi değiştir"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
