"use client";

import Link from "next/link";
import NavAuth from "@/components/NavAuth";
import PricingCalculator from "@/components/PricingCalculator";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";
import {
  Check,
  X,
  ArrowRight,
  Play,
  Mic,
  Users,
  Building2,
  Flame,
  Captions,
  Scissors,
  Frame,
} from "lucide-react";

function YouTubeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M21.6 7.2a2.5 2.5 0 0 0-1.76-1.77C18.27 5 12 5 12 5s-6.27 0-7.84.43A2.5 2.5 0 0 0 2.4 7.2C2 8.78 2 12 2 12s0 3.22.4 4.8a2.5 2.5 0 0 0 1.76 1.77C5.73 19 12 19 12 19s6.27 0 7.84-.43a2.5 2.5 0 0 0 1.76-1.77C22 15.22 22 12 22 12s0-3.22-.4-4.8ZM10 15V9l5.2 3L10 15Z" />
    </svg>
  );
}

const MOMENTS = [
  { label: "00:42 · Beklenmedik itiraf", score: 96 },
  { label: "12:08 · Tartışmalı fikir", score: 91 },
  { label: "27:55 · Komik anekdot", score: 84 },
];

const BENTO_CARDS = [
  {
    icon: Captions,
    accent: "bg-sky-400",
    ring: "bg-sky-400/10 text-sky-300 ring-sky-400/30",
    title: "Altyazı tam konuşmanın üstüne biner",
    desc: "Kelime kelime, ağızdan çıktığı anda ekranda. Premiere'de sürükleyip senkronlamakla uğraşmazsın.",
  },
  {
    icon: Scissors,
    accent: "bg-amber-400",
    ring: "bg-amber-400/10 text-amber-300 ring-amber-400/30",
    title: '"Şey", "ıı", "eee" uçar gider',
    desc: "Dolgu kelimeleri ve ölü sessizlikleri otomatik kırpıyoruz. Klip baştan sona akıcı çıkıyor.",
  },
  {
    icon: Frame,
    accent: "bg-violet-400",
    ring: "bg-violet-400/10 text-violet-300 ring-violet-400/30",
    title: "Kapak görseli hazır çıkar",
    desc: "Videodan en iyi kareyi kendimiz seçip başlığı üstüne koyuyoruz. Canva'yı açmana gerek yok.",
  },
  {
    icon: YouTubeIcon,
    accent: "bg-red-500",
    ring: "bg-red-500/10 text-red-400 ring-red-500/30",
    title: "Tek tıkla YouTube Shorts'a yükle",
    desc: "Kanalını bir kez bağla, klibi editörden doğrudan Shorts olarak yayınla. İndirip tekrar yüklemekle uğraşma.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Yükle",
    desc: "Podcast, röportaj ya da canlı yayın kaydını sürükle bırak, gerisi otomatik başlasın.",
  },
  {
    n: "02",
    title: "Yapay zeka izlesin",
    desc: "Konuşmayı dinler, en çarpıcı anları bulur, dikey formata kırpar ve altyazısını yakar.",
  },
  {
    n: "03",
    title: "İndir, paylaş",
    desc: "Hazır klipleri indir; doğrudan TikTok, Reels ya da Shorts'a yükle.",
  },
];

const PERSONAS = [
  {
    icon: Mic,
    title: "Podcast Yapımcıları",
    desc: "Saatlik bölümlerini, dinleyicinin sosyal medyada durup izleyeceği 30 saniyelik anlara indir.",
  },
  {
    icon: Users,
    title: "Influencer'lar",
    desc: "Uzun vlog ya da canlı yayın kayıtlarından viral olabilecek anları saniyeler içinde çıkar; kurgu ekibine ihtiyaç duymadan her gün yeni içerik paylaş.",
  },
  {
    icon: Building2,
    title: "Ajanslar",
    desc: "Onlarca müşterinin ham kaydını tek panelden işle — saatler değil dakikalar sürsün.",
  },
];

const STATS = [
  { value: "3-6", label: "klip / video" },
  { value: "~5 dk", label: "işlem süresi" },
  { value: "%100", label: "otomatik iş akışı" },
];

const COMPARISON = [
  { label: "Aylık başlangıç fiyatı", us: "Ücretsiz", opus: "$15", submagic: "$19" },
  { label: "Gelişmiş transkript kalitesi", us: true, opus: false, submagic: false },
  { label: "Otomatik dikey format", us: true, opus: true, submagic: true },
  { label: "Senkronize altyazı", us: true, opus: true, submagic: true },
];

const FAQ = [
  {
    q: "Hangi video formatlarını yükleyebilirim?",
    a: "MP4 başta olmak üzere yaygın kullanılan tüm video formatlarını yükleyebilirsin. Dosya boyutu ve süre sınırları planına göre değişir.",
  },
  {
    q: "Altyazılar hangi dilde çıkıyor?",
    a: "Klipster, videonun konuşulan dilini otomatik tespit eder ve altyazıyı o dilde üretir — Türkçe, İngilizce, Almanca fark etmez. Ayrıca her klip için İngilizce çevirili bir altyazı dosyası da ayrıca indirilebilir.",
  },
  {
    q: "Video başına kaç klip çıkıyor?",
    a: "Yapay zeka, videonun uzunluğuna ve içerik yoğunluğuna göre genelde 3 ile 6 arasında klip üretir. Bu sayı videodan videoya değişebilir.",
  },
  {
    q: "Klipleri istediğim platforma paylaşabilir miyim?",
    a: "Klipler standart MP4 formatında indirilir; TikTok, Instagram Reels, YouTube Shorts dahil istediğin her yere yükleyebilirsin.",
  },
  {
    q: "Ücretsiz planın sınırı ne?",
    a: "Ücretsiz planda ayda 2 video işleyebilir, video başına 4 klip elde edebilirsin. Daha fazlası için Yaratıcı veya Ajans planlarına geçebilirsin.",
  },
];

export default function LandingPage() {
  return (
    <div className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      {/* Global koyu arka plan: parallax yildizlar + grid + turuncu isik */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0202] to-black" />
        <ParallaxStars speed={1} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-red-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="noir-gradient-blur" />

      {/* Navbar - kirmizi tema ile uyumlu cerceve + yumusak halo parlamasi */}
      <header className="fixed top-0 left-0 w-full z-50 pt-6 px-4">
        <div className="max-w-5xl mx-auto relative">
          <div className="absolute -inset-2 rounded-full bg-red-600/20 blur-xl animate-glow pointer-events-none" />
          <nav className="relative flex items-center justify-between bg-black/60 backdrop-blur-xl border border-red-500/25 rounded-full px-6 py-3 shadow-[0_0_25px_rgba(239,68,68,0.15)] transition-all duration-500 hover:border-red-500/45 hover:shadow-[0_0_35px_rgba(239,68,68,0.25)]">
            <Link
              href="/"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              className="flex items-center gap-2"
            >
              <Logo className="h-14" />
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <a href="#ozellikler" className="relative text-sm font-medium text-zinc-400 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1.5 after:h-[1.5px] after:w-0 after:bg-red-500 after:transition-all after:duration-300 hover:after:w-full">
                Özellikler
              </a>
              <a href="#nasil-calisir" className="relative text-sm font-medium text-zinc-400 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1.5 after:h-[1.5px] after:w-0 after:bg-red-500 after:transition-all after:duration-300 hover:after:w-full">
                Nasıl Çalışır
              </a>
              <a href="#karsilastirma" className="relative text-sm font-medium text-zinc-400 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1.5 after:h-[1.5px] after:w-0 after:bg-red-500 after:transition-all after:duration-300 hover:after:w-full">
                Karşılaştırma
              </a>
              <a href="#fiyatlandirma" className="relative text-sm font-medium text-zinc-400 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1.5 after:h-[1.5px] after:w-0 after:bg-red-500 after:transition-all after:duration-300 hover:after:w-full">
                Fiyatlandırma
              </a>
              <Link href="/app" className="relative text-sm font-medium text-zinc-400 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1.5 after:h-[1.5px] after:w-0 after:bg-red-500 after:transition-all after:duration-300 hover:after:w-full">
                Video Oluştur
              </Link>
            </div>

            <NavAuth />
          </nav>
        </div>
      </header>

      <main className="relative z-10">
        {/* Hero */}
        <section className="min-h-screen flex flex-col items-center justify-center pt-40 pb-20 px-6">
          <div className="text-center max-w-5xl mx-auto">

            <h1 className="font-display text-5xl sm:text-7xl md:text-8xl font-bold tracking-tighter leading-[0.98] mb-8 animate-fade-up delay-1">
              <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40">
                Bir video yükle,
              </span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40">
                <span className="text-red-500 inline-block relative">
                  viral klipler çıksın
                  <svg
                    className="absolute w-full h-3 -bottom-2 left-0 text-red-500 opacity-60"
                    viewBox="0 0 100 10"
                    preserveAspectRatio="none"
                  >
                    <path d="M0 5 Q 50 10 100 5" stroke="currentColor" strokeWidth="2" fill="none" />
                  </svg>
                </span>
                .
              </span>
            </h1>

            <p className="text-lg md:text-2xl text-zinc-400 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-up delay-2">
              Videonu yükle, dakikalar içinde TikTok/Reels/Shorts&apos;a hazır,
              altyazılı klipler al.
            </p>

            <div className="flex flex-col md:flex-row items-center justify-center gap-4 animate-fade-up delay-3">
              <Link href="/kayit" className="noir-shiny-cta group">
                <span className="relative z-10 flex items-center gap-2 text-white font-medium">
                  Ücretsiz Dene
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
              <a
                href="#nasil-calisir"
                className="group px-8 py-4 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-300 font-medium hover:text-white hover:bg-zinc-800 transition-all flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Nasıl çalışır?
              </a>
            </div>
          </div>
        </section>

        {/* Stat strip */}
        <section className="border-y border-white/5 bg-white/[0.02] backdrop-blur-sm">
          <div className="max-w-5xl mx-auto px-6 py-12 grid grid-cols-3 divide-x divide-white/10 text-center">
            {STATS.map((s) => (
              <div key={s.label}>
                <p className="font-display text-3xl sm:text-4xl font-bold text-white">{s.value}</p>
                <p className="text-xs text-zinc-500 mt-1.5 uppercase tracking-widest">{s.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features bento grid */}
        <section id="ozellikler" className="py-32 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="mb-16 text-center max-w-2xl mx-auto">
              <h2 className="text-4xl md:text-5xl font-semibold text-white tracking-tight font-display mb-6">
                Kurgu masana <br />
                <span className="text-red-500">gerek yok</span>
              </h2>
              <p className="text-lg text-zinc-400 font-light">
                Manuel kurgu ve altyazılamaya harcadığın zamanı geri kazan.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-auto lg:h-[640px]">
              {/* Ana kart */}
              <div className="md:col-span-2 lg:row-span-2 relative overflow-hidden p-8 rounded-2xl border border-white/10 bg-gradient-to-br from-red-950/30 via-zinc-950 to-black">
                <div className="relative z-10 h-full flex flex-col">
                  <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-400 ring-1 ring-red-500/30">
                    <Flame className="w-6 h-6" />
                  </div>
                  <h3 className="text-3xl font-semibold text-white font-display mb-4 tracking-tight">
                    Hangi anın patlayacağını biz buluruz
                  </h3>
                  <p className="text-zinc-400 text-lg leading-relaxed">
                    2 saatlik videoyu baştan sona izlemene gerek yok. Klipster konuşmayı dinler,
                    en çok konuşulacak anları saniyeler içinde çıkarır ve sana sırayla sunar.
                  </p>
                  <div className="mt-auto pt-8 space-y-3">
                    {MOMENTS.map((m) => (
                      <div key={m.label} className="rounded-lg border border-white/10 bg-black/40 px-4 py-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-zinc-300">{m.label}</span>
                          <span className="font-mono text-red-400">{m.score}</span>
                        </div>
                        <div className="mt-2 h-1 rounded-full bg-white/10">
                          <div className="h-1 rounded-full bg-red-500" style={{ width: `${m.score}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Ozellik kartlari */}
              {BENTO_CARDS.map((f, i) => (
                <div
                  key={f.title}
                  className="group relative overflow-hidden p-6 rounded-2xl border border-white/10 bg-zinc-950 hover:border-white/25 hover:-translate-y-1 transition-all duration-300"
                >
                  <div className={`absolute left-0 top-0 h-full w-0.5 ${f.accent} opacity-60 group-hover:opacity-100 transition-opacity`} />
                  <div className="flex items-start justify-between mb-5">
                    <div className={`inline-flex h-11 w-11 items-center justify-center rounded-full ring-1 ${f.ring}`}>
                      <f.icon className="w-5 h-5" />
                    </div>
                    <span className="font-mono text-xs text-zinc-600">0{i + 1}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-white font-display mb-2 leading-snug">{f.title}</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Kimler icin */}
        <section className="border-y border-white/5 bg-white/[0.02]">
          <div className="max-w-6xl mx-auto px-6 py-24">
            <div className="max-w-xl mb-14">
              <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Kimler için?</h2>
              <p className="mt-4 text-zinc-400">Elinde uzun ham içerik olan herkes için tasarlandı.</p>
            </div>
            <div className="grid sm:grid-cols-3 gap-6">
              {PERSONAS.map((p) => (
                <div
                  key={p.title}
                  className="bg-black border border-white/10 hover:border-red-500/30 hover:-translate-y-1 transition-all duration-300 rounded-2xl p-8"
                >
                  <p.icon className="h-5 w-5 text-red-500" />
                  <h3 className="font-semibold mt-4 text-white">{p.title}</h3>
                  <p className="mt-2 text-sm text-zinc-400 leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Nasil calisir */}
        <section id="nasil-calisir" className="py-24 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="max-w-xl mb-14">
              <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Üç adımda hazır</h2>
              <p className="mt-4 text-zinc-400">Karmaşık bir video editörü öğrenmene gerek yok.</p>
            </div>
            <div className="grid sm:grid-cols-3 gap-10">
              {STEPS.map((s) => (
                <div key={s.n} className="border-t border-white/10 pt-6">
                  <span className="font-mono text-sm text-red-500">{s.n}</span>
                  <h3 className="font-semibold text-lg mt-3 text-white">{s.title}</h3>
                  <p className="mt-2 text-sm text-zinc-400 leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Marka bandı */}
        <div className="w-full bg-red-500 py-20 px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h3 className="text-3xl md:text-5xl font-bold text-black font-display leading-tight">
              Kurguyla geçirdiğin saatler artık dakikalar.
            </h3>
            <p className="mt-6 text-black/70 font-medium max-w-lg mx-auto">
              Klipster; transkript çıkarmayı, en ilgi çekici anı bulmayı, dikey formata kırpmayı ve
              altyazı yakmayı tek bir otomatik hatta topluyor.
            </p>
          </div>
        </div>

        {/* Karsilastirma */}
        <section id="karsilastirma" className="max-w-6xl mx-auto px-6 py-24">
          <div className="max-w-xl mb-14">
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Neden Klipster?</h2>
            <p className="mt-4 text-zinc-400">
              Aynı işi yapan araçlar var — farkımız hız, netlik ve şeffaf fiyatlandırma.
            </p>
          </div>
          <div className="overflow-x-auto border border-white/10 rounded-2xl">
            <table className="w-full text-sm min-w-[560px]">
              <thead>
                <tr className="border-b border-white/10 bg-white/[0.03]">
                  <th className="text-left font-medium text-zinc-500 px-6 py-4">&nbsp;</th>
                  <th className="text-center font-semibold px-6 py-4 text-red-500">Klipster</th>
                  <th className="text-center font-medium text-zinc-500 px-6 py-4">Opus Clip</th>
                  <th className="text-center font-medium text-zinc-500 px-6 py-4">Submagic</th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON.map((row, i) => (
                  <tr key={row.label} className={i !== COMPARISON.length - 1 ? "border-b border-white/5" : ""}>
                    <td className="px-6 py-4 text-zinc-300">{row.label}</td>
                    <td className="px-6 py-4 text-center font-medium text-white">
                      {typeof row.us === "boolean" ? (
                        row.us ? (
                          <Check className="h-4 w-4 text-red-500 inline" />
                        ) : (
                          <X className="h-4 w-4 text-zinc-700 inline" />
                        )
                      ) : (
                        row.us
                      )}
                    </td>
                    <td className="px-6 py-4 text-center text-zinc-500">
                      {typeof row.opus === "boolean" ? (
                        row.opus ? (
                          <Check className="h-4 w-4 text-zinc-500 inline" />
                        ) : (
                          <X className="h-4 w-4 text-zinc-700 inline" />
                        )
                      ) : (
                        row.opus
                      )}
                    </td>
                    <td className="px-6 py-4 text-center text-zinc-500">
                      {typeof row.submagic === "boolean" ? (
                        row.submagic ? (
                          <Check className="h-4 w-4 text-zinc-500 inline" />
                        ) : (
                          <X className="h-4 w-4 text-zinc-700 inline" />
                        )
                      ) : (
                        row.submagic
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-zinc-600">
            Rakip fiyatları kamuya açık kaynaklardan alınmıştır, Ağustos 2026 itibarıyla.
          </p>
        </section>

        <PricingCalculator />

        {/* SSS */}
        <section className="max-w-3xl mx-auto px-6 py-24">
          <div className="mb-10">
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Sık sorulan sorular</h2>
          </div>
          <div className="divide-y divide-white/10 border-t border-b border-white/10">
            {FAQ.map((item) => (
              <details key={item.q} className="group py-5">
                <summary className="flex items-center justify-between cursor-pointer list-none font-medium text-white">
                  {item.q}
                  <span className="text-zinc-500 group-open:rotate-45 transition-transform text-xl leading-none">
                    +
                  </span>
                </summary>
                <p className="mt-3 text-sm text-zinc-400 leading-relaxed">{item.a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-32 px-6 text-center">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-5xl md:text-7xl font-bold font-display mb-8 tracking-tighter">
              Viral anın <span className="text-red-500">videonun içinde</span> bekliyor.
            </h2>
            <p className="text-xl text-zinc-400 mb-12">Kredi kartı gerekmez, kayıt saniyeler sürer.</p>
            <Link href="/kayit" className="noir-shiny-cta group inline-flex">
              <span className="relative z-10 flex items-center gap-2 text-white font-medium">
                Ücretsiz Dene
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </span>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-black border-t border-zinc-900 pt-20 pb-10 relative overflow-hidden z-10">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-5 gap-12 mb-20 relative z-10">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-6">
              <Logo className="h-16" />
            </div>
            <p className="text-zinc-500 max-w-xs leading-relaxed">
              İçerik üreticiler için sıfırdan tasarlanan yapay zeka klip stüdyosu.
            </p>
            <div className="flex items-center gap-4 mt-6">
              <a
                href="https://www.instagram.com/klipster.tr"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
                className="text-zinc-500 hover:text-red-500 transition-colors"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <rect x="3" y="3" width="18" height="18" rx="5" />
                  <circle cx="12" cy="12" r="4" />
                  <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none" />
                </svg>
              </a>
              <a
                href="https://x.com/klipstertr"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="X (Twitter)"
                className="text-zinc-500 hover:text-red-500 transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.045 4.126H5.078z" />
                </svg>
              </a>
              <a
                href="https://www.tiktok.com/@klipster.tr"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="TikTok"
                className="text-zinc-500 hover:text-red-500 transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M16.6 5.82a4.28 4.28 0 0 1-3.34-4.05h-3.22v13.9a2.6 2.6 0 1 1-2.6-2.6c.14 0 .27.01.4.03V9.9a5.86 5.86 0 0 0-.4-.01 5.86 5.86 0 1 0 5.86 5.86V9.1a7.5 7.5 0 0 0 4.3 1.36V7.24a4.27 4.27 0 0 1-1-1.42z" />
                </svg>
              </a>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-red-500 uppercase tracking-widest mb-6">Ürün</h4>
            <ul className="space-y-4 text-zinc-400 text-sm">
              <li><a href="#ozellikler" className="hover:text-white transition-colors">Özellikler</a></li>
              <li><a href="#nasil-calisir" className="hover:text-white transition-colors">Nasıl Çalışır</a></li>
              <li><a href="#fiyatlandirma" className="hover:text-white transition-colors">Fiyatlandırma</a></li>
              <li><a href="#karsilastirma" className="hover:text-white transition-colors">Karşılaştırma</a></li>
              <li><Link href="/blog" className="hover:text-white transition-colors">Rehberler</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-red-500 uppercase tracking-widest mb-6">Hesap</h4>
            <ul className="space-y-4 text-zinc-400 text-sm">
              <li><Link href="/giris" className="hover:text-white transition-colors">Giriş Yap</Link></li>
              <li><Link href="/kayit" className="hover:text-white transition-colors">Üye Ol</Link></li>
              <li><Link href="/app" className="hover:text-white transition-colors">Panel</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-red-500 uppercase tracking-widest mb-6">Yasal</h4>
            <ul className="space-y-4 text-zinc-400 text-sm">
              <li><Link href="/gizlilik-politikasi" className="hover:text-white transition-colors">Gizlilik Politikası</Link></li>
              <li><Link href="/kullanim-kosullari" className="hover:text-white transition-colors">Kullanım Koşulları</Link></li>
              <li><Link href="/iletisim" className="hover:text-white transition-colors">İletişim &amp; SSS</Link></li>
            </ul>
          </div>
        </div>

        {/* Dev footer yazisi */}
        <div className="flex justify-center items-center py-6 opacity-20 pointer-events-none">
          <h1 className="text-[15vw] leading-none font-bold font-display tracking-tighter noir-text-stroke select-none">
            KLIPSTER
          </h1>
        </div>

        <div className="max-w-7xl mx-auto px-6 border-t border-zinc-900 pt-8 flex flex-col md:flex-row items-center justify-between text-zinc-600 text-[10px] uppercase tracking-widest">
          <p>© 2026 Klipster</p>
          <p className="mt-4 md:mt-0">Yapay zeka destekli klip stüdyosu</p>
        </div>
      </footer>
    </div>
  );
}
