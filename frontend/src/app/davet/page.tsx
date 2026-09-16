"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, Users, XCircle } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DavetPage() {
  return (
    <Suspense fallback={null}>
      <DavetContent />
    </Suspense>
  );
}

type Status = "checking" | "need-auth" | "accepting" | "accepted" | "error";

function DavetContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<Status>("checking");
  const [orgName, setOrgName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // React StrictMode gelistirme modunda useEffect'i mount'ta iki kere calistirir -
  // bu ref olmadan ikinci istekte davet zaten kabul edilmis oldugu icin
  // yanlislikla hata gorunurdu (ilk istek aslinda basarili olsa bile).
  const requestedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Davet bağlantısı geçersiz - token eksik");
      return;
    }

    const authToken = localStorage.getItem("klipster_token");
    if (!authToken) {
      setStatus("need-auth");
      return;
    }

    if (requestedRef.current === token) return;
    requestedRef.current = token;

    setStatus("accepting");
    fetch(`${API_URL}/api/org/accept-invite`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || "Davet kabul edilemedi");
        return data;
      })
      .then((data: { org_name: string | null }) => {
        setOrgName(data.org_name);
        setStatus("accepted");
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
          {status === "checking" || status === "accepting" ? (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                <Users className="h-5 w-5 text-orange-400 animate-pulse" />
              </div>
              <p className="mt-4 text-sm text-zinc-400">Davet kontrol ediliyor...</p>
            </>
          ) : status === "need-auth" ? (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                <Users className="h-5 w-5 text-orange-400" />
              </div>
              <h1 className="mt-4 text-lg font-display font-semibold">Bir ekibe davet edildin</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Daveti kabul etmek için önce giriş yap ya da hesap oluştur.
              </p>
              <div className="mt-6 flex flex-col gap-3">
                <Link
                  href={`/giris?invite=${token ?? ""}`}
                  className="bg-orange-500 hover:bg-orange-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition"
                >
                  Giriş yap
                </Link>
                <Link
                  href={`/kayit?invite=${token ?? ""}`}
                  className="bg-white/10 hover:bg-white/15 text-white px-6 py-2.5 rounded-full font-semibold text-sm transition"
                >
                  Hesap oluştur
                </Link>
              </div>
            </>
          ) : status === "accepted" ? (
            <>
              <div className="mx-auto h-12 w-12 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <h1 className="mt-4 text-lg font-display font-semibold">
                {orgName ? `${orgName} ekibine katıldın` : "Ekibe katıldın"}
              </h1>
              <p className="mt-2 text-sm text-zinc-400">
                Artık ekibin video/klip geçmişini görebilir ve plan haklarından faydalanabilirsin.
              </p>
              <button
                onClick={() => router.push("/profil")}
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
              <h1 className="mt-4 text-lg font-display font-semibold">Davet kabul edilemedi</h1>
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
