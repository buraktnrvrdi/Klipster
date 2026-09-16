"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SifremiUnuttumPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Bir şeyler ters gitti");
        return;
      }
      setSent(true);
    } catch {
      setError("Sunucuya ulaşılamadı, backend çalışıyor mu kontrol et");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="noir-selection relative min-h-screen bg-black text-white flex items-center justify-center px-6 overflow-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0202] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-red-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        <Link href="/" className="flex items-center gap-2 w-fit">
          <Logo className="h-14" />
        </Link>

        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl">
          {sent ? (
            <>
              <div className="h-12 w-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <Mail className="h-5 w-5 text-red-400" />
              </div>
              <h1 className="mt-4 text-xl font-semibold font-display tracking-tight">E-postanı kontrol et</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Eğer <span className="text-zinc-200">{email}</span> kayıtlıysa, şifreni sıfırlaman için bir
                bağlantı gönderdik. Gelen kutunu (ve spam klasörünü) kontrol et.
              </p>
              <Link
                href="/giris"
                className="mt-6 inline-block bg-white/10 hover:bg-white/15 text-white px-5 py-2.5 rounded-full text-sm font-semibold transition"
              >
                Girişe dön
              </Link>
            </>
          ) : (
            <>
              <h1 className="text-2xl font-semibold font-display tracking-tight">Şifreni sıfırla</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Hesabına kayıtlı e-posta adresini gir, sana bir sıfırlama bağlantısı gönderelim.
              </p>

              <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
                <label className="text-sm">
                  <span className="block mb-1.5 text-zinc-400 font-medium">E-posta</span>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                    placeholder="ornek@mail.com"
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
                  className="mt-2 bg-red-500 hover:bg-red-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
                >
                  {loading ? "Gönderiliyor..." : "Sıfırlama linki gönder"}
                </button>
                <Link href="/giris" className="text-center text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
                  Girişe dön
                </Link>
              </form>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
