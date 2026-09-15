"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Mail } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function KayitPage() {
  return (
    <Suspense fallback={null}>
      <KayitForm />
    </Suspense>
  );
}

function KayitForm() {
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Kayıt başarısız");
        return;
      }
      // Hesap olusturuldu ama henuz oturum acilmadi - once e-postayi
      // dogrulamasi gerekiyor. Bir ekip davetinden geldiyse, dogrulama
      // sonrasi davete geri donebilmesi icin token'i sakliyoruz.
      if (inviteToken) {
        localStorage.setItem("klipster_pending_invite", inviteToken);
      }
      setRegistered(true);
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
          {registered ? (
            <>
              <div className="h-12 w-12 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                <Mail className="h-5 w-5 text-orange-400" />
              </div>
              <h1 className="mt-4 text-xl font-semibold font-display tracking-tight">E-postanı kontrol et</h1>
              <p className="mt-2 text-sm text-zinc-400">
                <span className="text-zinc-200">{email}</span> adresine bir doğrulama bağlantısı
                gönderdik. Hesabını kullanmaya başlamak için gelen kutunu (ve spam klasörünü) kontrol
                edip bağlantıya tıklaman gerekiyor.
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
          <h1 className="text-2xl font-semibold font-display tracking-tight">Klipster&apos;a katıl</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Zaten hesabın var mı?{" "}
            <Link
              href={inviteToken ? `/giris?invite=${inviteToken}` : "/giris"}
              className="text-orange-500 font-medium hover:underline"
            >
              Giriş yap
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
              <span className="block mb-1.5 text-zinc-400 font-medium">Şifre</span>
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
              {loading ? "Hesap oluşturuluyor..." : "Ücretsiz hesap oluştur"}
            </button>
            <p className="text-xs text-zinc-500 text-center">
              Kredi kartı gerekmez · Ücretsiz planla ayda 2 video
            </p>
          </form>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
