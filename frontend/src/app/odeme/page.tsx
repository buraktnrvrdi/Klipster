"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const inputCls =
  "w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors";

type PlanInfo = { id: string; label: string; price_try: number; price_usd: number };

export default function OdemePage() {
  return (
    <Suspense fallback={null}>
      <OdemeForm />
    </Suspense>
  );
}

function OdemeForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan") || "yaratici";

  const [token, setToken] = useState<string | null>(null);
  const [plans, setPlans] = useState<PlanInfo[] | null>(null);
  const [name, setName] = useState("");
  const [surname, setSurname] = useState("");
  const [phone, setPhone] = useState("");
  const [identityNumber, setIdentityNumber] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkoutFormContent, setCheckoutFormContent] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("klipster_token");
    if (!t) {
      router.push(`/giris?next=${encodeURIComponent(`/odeme?plan=${planId}`)}`);
      return;
    }
    setToken(t);
  }, [router, planId]);

  useEffect(() => {
    fetch(`${API_URL}/api/payments/plans`)
      .then((r) => r.json())
      .then((d) => setPlans(d.plans || []))
      .catch(() => setPlans([]));
  }, []);

  // iyzico'nun checkout_form_content'i bir <script> etiketi olarak geliyor -
  // React'in dangerouslySetInnerHTML'i script'leri calistirmadigi icin,
  // script gövdesini elle çıkarıp document'e ekliyoruz. iyzico'nun kendi
  // kodu calisirken "iyzipay-checkout-form" id'li div'i bulup icine
  // odeme formunu (iframe) yerlestiriyor.
  useEffect(() => {
    if (!checkoutFormContent) return;
    const match = checkoutFormContent.match(/<script[^>]*>([\s\S]*?)<\/script>/i);
    const scriptBody = match ? match[1] : checkoutFormContent;
    const script = document.createElement("script");
    script.type = "text/javascript";
    script.text = scriptBody;
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, [checkoutFormContent]);

  const selectedPlan = plans?.find((p) => p.id === planId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/payments/checkout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: planId,
          name,
          surname,
          phone,
          identity_number: identityNumber,
          address,
          city,
          zip_code: zipCode,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Ödeme başlatılamadı");
        return;
      }
      setCheckoutFormContent(data.checkout_form_content);
    } catch {
      setError("Sunucuya ulaşılamadı, lütfen tekrar dene");
    } finally {
      setLoading(false);
    }
  }

  if (!token) return null;

  return (
    <main className="noir-selection relative min-h-screen bg-black text-white px-6 py-16 overflow-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0202] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-red-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="relative z-10 max-w-lg mx-auto">
        <Link href="/" className="flex items-center justify-center mb-2">
          <Logo className="h-20" />
        </Link>
        <Link
          href="/profil"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors mb-6"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Profile dön
        </Link>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 shadow-2xl">
          {!checkoutFormContent ? (
            <>
              <h1 className="text-2xl font-semibold font-display tracking-tight">
                {selectedPlan ? selectedPlan.label : "Plan"} planına geç
              </h1>
              <p className="mt-2 text-sm text-zinc-400">
                {selectedPlan
                  ? `Aylık $${selectedPlan.price_usd} - otomatik yenilenir, istediğin zaman iptal edebilirsin.`
                  : plans && plans.length === 0
                  ? "Ödeme sistemi şu anda kullanılamıyor, lütfen daha sonra tekrar dene."
                  : "Plan bilgisi yükleniyor..."}
              </p>

              <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <label className="text-sm">
                    <span className="block mb-1.5 text-zinc-400 font-medium">Ad</span>
                    <input required value={name} onChange={(e) => setName(e.target.value)} className={inputCls} />
                  </label>
                  <label className="text-sm">
                    <span className="block mb-1.5 text-zinc-400 font-medium">Soyad</span>
                    <input required value={surname} onChange={(e) => setSurname(e.target.value)} className={inputCls} />
                  </label>
                </div>
                <label className="text-sm">
                  <span className="block mb-1.5 text-zinc-400 font-medium">Telefon</span>
                  <input
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+90 5xx xxx xx xx"
                    className={inputCls}
                  />
                </label>
                <label className="text-sm">
                  <span className="block mb-1.5 text-zinc-400 font-medium">TC Kimlik No (opsiyonel)</span>
                  <input
                    value={identityNumber}
                    onChange={(e) => setIdentityNumber(e.target.value)}
                    maxLength={11}
                    className={inputCls}
                  />
                </label>
                <label className="text-sm">
                  <span className="block mb-1.5 text-zinc-400 font-medium">Adres</span>
                  <input required value={address} onChange={(e) => setAddress(e.target.value)} className={inputCls} />
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <label className="text-sm">
                    <span className="block mb-1.5 text-zinc-400 font-medium">Şehir</span>
                    <input required value={city} onChange={(e) => setCity(e.target.value)} className={inputCls} />
                  </label>
                  <label className="text-sm">
                    <span className="block mb-1.5 text-zinc-400 font-medium">Posta Kodu</span>
                    <input value={zipCode} onChange={(e) => setZipCode(e.target.value)} className={inputCls} />
                  </label>
                </div>

                <label className="flex items-start gap-2.5 text-xs text-zinc-400 select-none">
                  <input
                    type="checkbox"
                    required
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="mt-0.5 h-3.5 w-3.5 shrink-0 accent-red-500"
                  />
                  <span>
                    <Link href="/kullanim-kosullari" target="_blank" className="text-red-400 hover:underline">
                      Kullanım Koşulları&apos;nı
                    </Link>{" "}
                    okudum, kabul ediyorum ve hizmetin ifasına derhal başlanmasını onayladığım için
                    cayma hakkımı kullanamayacağımı biliyorum.
                  </span>
                </label>

                {error && (
                  <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || !selectedPlan || !termsAccepted}
                  className="mt-2 bg-red-500 hover:bg-red-600 text-black px-6 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
                >
                  {loading ? "Hazırlanıyor..." : "Ödemeye geç"}
                </button>
                <p className="flex items-center gap-1.5 text-xs text-zinc-500 justify-center mt-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> Kart bilgilerin iyzico&apos;nun güvenli sayfasında işlenir,
                  bizde saklanmaz.
                </p>
              </form>
            </>
          ) : (
            <div>
              <h1 className="text-xl font-semibold font-display tracking-tight mb-4">Kart bilgilerini gir</h1>
              <div id="iyzipay-checkout-form" className="responsive" />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
