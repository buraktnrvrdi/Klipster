"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Mail } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function EmailDogrulaPage() {
  return (
    <Suspense fallback={null}>
      <EmailDogrulaContent />
    </Suspense>
  );
}

function EmailDogrulaContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

  function goNext() {
    const pendingInvite = localStorage.getItem("klipster_pending_invite");
    if (pendingInvite) {
      localStorage.removeItem("klipster_pending_invite");
      router.push(`/davet?token=${pendingInvite}`);
    } else {
      router.push("/app");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/auth/verify-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Doğrulanamadı");
        return;
      }
      if (data.token) {
        localStorage.setItem("klipster_token", data.token);
      }
      goNext();
    } catch {
      setError("Sunucuya ulaşılamadı, backend çalışıyor mu kontrol et");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setResending(true);
    setError(null);
    try {
      await fetch(`${API_URL}/api/auth/resend-verification-public`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setResent(true);
    } catch {
      // sessizce yoksay
    } finally {
      setResending(false);
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
        <Link href="/" className="flex items-center justify-center">
          <Logo className="h-24" />
        </Link>

        <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl text-center">
          {!email ? (
            <>
              <h1 className="text-xl font-semibold font-display tracking-tight">Bağlantı geçersiz</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Bu sayfaya bir e-posta adresi olmadan ulaştın.
              </p>
              <Link
                href="/kayit"
                className="mt-6 inline-block bg-white/10 hover:bg-white/15 text-white px-6 py-2.5 rounded-full font-semibold text-sm transition"
              >
                Kayıt sayfasına dön
              </Link>
            </>
          ) : (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <Mail className="h-5 w-5 text-red-400" />
              </div>
              <h1 className="mt-4 text-xl font-semibold font-display tracking-tight">E-postanı doğrula</h1>
              <p className="mt-2 text-sm text-zinc-400">
                <span className="text-zinc-200">{email}</span> adresine 6 haneli bir kod gönderdik.
                Gelen kutunu (ve spam klasörünü) kontrol edip kodu aşağıya gir.
              </p>

              <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4 text-left">
                <input
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  required
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-center text-lg tracking-[0.5em] text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                  placeholder="000000"
                />

                {error && (
                  <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    {error}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="bg-red-500 hover:bg-red-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
                >
                  {loading ? "Doğrulanıyor..." : "Doğrula"}
                </button>
              </form>

              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="mt-4 text-xs font-semibold text-zinc-400 hover:text-white transition-colors disabled:opacity-40"
              >
                {resent ? "Kod tekrar gönderildi ✓" : resending ? "Gönderiliyor..." : "Kodu tekrar gönder"}
              </button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
