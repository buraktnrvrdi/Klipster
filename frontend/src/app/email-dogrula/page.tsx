"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, Mail, XCircle } from "lucide-react";
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

type Status = "checking" | "success" | "error";

function EmailDogrulaContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<Status>("checking");
  const [error, setError] = useState<string | null>(null);
  // React StrictMode gelistirme modunda useEffect'i mount'ta bilerek iki kere
  // calistirir - bu ref olmadan token ikinci istekte zaten silinmis oldugu
  // icin yanlislikla "gecersiz" hatasi gorunurdu (istek aslinda basarili olsa bile).
  const requestedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Doğrulama bağlantısı geçersiz - token eksik");
      return;
    }
    if (requestedRef.current === token) return;
    requestedRef.current = token;

    fetch(`${API_URL}/api/auth/verify-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || "Doğrulanamadı");
        // Dogrulama linkine tiklamak artik otomatik giris de yapiyor (backend
        // token dondurur) - kullaniciyi tekrar giris yapmaya zorlamiyoruz.
        if (data.token) {
          localStorage.setItem("klipster_token", data.token);
        }
        setStatus("success");
      })
      .catch((e: Error) => {
        setStatus("error");
        setError(e.message);
      });
  }, [token]);

  return (
    <main className="noir-selection relative min-h-screen bg-black text-white flex items-center justify-center px-6 overflow-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0d02] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-orange-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="relative z-10 w-full max-w-sm text-center">
        <Link href="/" className="flex items-center gap-2 w-fit mx-auto">
          <Logo className="h-9" />
        </Link>

        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl">
          {status === "checking" ? (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                <Mail className="h-5 w-5 text-orange-400 animate-pulse" />
              </div>
              <p className="mt-4 text-sm text-zinc-400">Doğrulanıyor...</p>
            </>
          ) : status === "success" ? (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <h1 className="mt-4 text-lg font-display font-semibold">E-postan doğrulandı</h1>
              <p className="mt-2 text-sm text-zinc-400">Artık hesabının tüm özelliklerine erişebilirsin.</p>
              <button
                onClick={() => {
                  const pendingInvite = localStorage.getItem("klipster_pending_invite");
                  if (pendingInvite) {
                    localStorage.removeItem("klipster_pending_invite");
                    router.push(`/davet?token=${pendingInvite}`);
                  } else {
                    router.push("/profil");
                  }
                }}
                className="mt-6 bg-orange-500 hover:bg-orange-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition"
              >
                Profilime git
              </button>
            </>
          ) : (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <XCircle className="h-5 w-5 text-red-400" />
              </div>
              <h1 className="mt-4 text-lg font-display font-semibold">Doğrulanamadı</h1>
              <p className="mt-2 text-sm text-red-400">{error}</p>
              <Link
                href="/profil"
                className="mt-6 inline-block bg-white/10 hover:bg-white/15 text-white px-6 py-2.5 rounded-full font-semibold text-sm transition"
              >
                Profilime git
              </Link>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
