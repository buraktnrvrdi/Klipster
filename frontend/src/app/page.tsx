"use client";

import Link from "next/link";
import NavAuth from "@/components/NavAuth";
import PricingCalculator from "@/components/PricingCalculator";
import ParallaxStars from "@/components/ParallaxStars";
import {
  Sparkles,
  MessageSquareText,
  Check,
  X,
  ArrowRight,
  Play,
  Mic,
  Users,
  Building2,
  Wand2,
  Image as ImageIcon,
} from "lucide-react";

const BENTO_SECONDARY = [
  {
    icon: MessageSquareText,
    color: "text-blue-400",
    title: "Kelimesi kelimesine altyazı",
    desc: "Konuşmayla aynı anda beliren, taşmayan, okunaklı altyazılar — elle senkronize etmene gerek kalmaz.",
  },
  {
    icon: Wand2,
    color: "text-yellow-400",
    title: "Dolgu kelime temizliği",
    desc: '"Şey", "ıı", "eee" ve uzun sessizlikler otomatik kırpılır; klip akıcı ve dinlenebilir çıkar.',
  },
  {
    icon: ImageIcon,
    color: "text-purple-400",
    title: "Otomatik kapak görseli",
    desc: "Videonun içinden en güçlü kareyi seçip başlığı üstüne bindirir. Kapak tasarımıyla uğraşmazsın.",
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
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0d02] to-black" />
        <ParallaxStars speed={1} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-orange-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <div className="noir-gradient-blur" />

      {/* Navbar */}
      <header className="fixed top-0 left-0 w-full z-50 pt-6 px-4">
        <nav className="max-w-5xl mx-auto flex items-center justify-between bg-black/60 backdrop-blur-xl border border-white/10 rounded-full px-6 py-3 shadow-2xl">
          <Link
            href="/"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="flex items-center gap-2"
          >
            <div className="w-5 h-5 bg-orange-500 rounded-sm rotate-45" />
            <span className="text-lg font-bold font-display tracking-tight">Klipster</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#ozellikler" className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
              Özellikler
            </a>
            <a href="#nasil-calisir" className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
              Nasıl Çalışır
            </a>
            <a href="#karsilastirma" className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
              Karşılaştırma
            </a>
            <a href="#fiyatlandirma" className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
              Fiyatlandırma
            </a>
            <Link href="/app" className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
              Video Oluştur
            </Link>
          </div>

          <NavAuth />
        </nav>
      </header>

      <main className="relative z-10">
        {/* Hero */}
        <section className="min-h-screen flex flex-col items-center justify-center pt-40 pb-20 px-6">
          <div className="text-center max-w-5xl mx-auto">

            <h1 className="font-display text-5xl sm:text-7xl md:text-8xl font-bold tracking-tighter leading-[0.98] mb-8 animate-fade-up delay-1">
              <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40">
                Konuş, kaydet,
              </span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40">
                <span className="text-orange-500 inline-block relative">
                  gerisini bize bırak
                  <svg
                    className="absolute w-full h-3 -bottom-2 left-0 text-orange-500 opacity-60"
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
              Klipster; podcast, röportaj ve yayın kayıtlarını analiz eder, en çarpıcı anları
              belirler, dikey formata dönüştürür ve altyazısını otomatik olarak ekler.
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
                <span className="text-orange-500">gerek yok</span>
              </h2>
              <p className="text-lg text-zinc-400 font-light">
                Manuel kurgu ve altyazılamaya harcadığın zamanı geri kazan.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-auto lg:h-[640px]">
              {/* Buyuk oncu kart */}
              <div className="lg:col-span-2 lg:row-span-2 group relative overflow-hidden p-8 border border-white/10 bg-gradient-to-b from-zinc-900/60 to-black hover:border-white/20 transition-all rounded-xl">
                <div className="relative z-10 h-full flex flex-col">
                  <div className="mb-6 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 text-orange-500 w-fit">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h3 className="text-3xl font-semibold text-white font-display mb-4 tracking-tight">
                    Yapay zeka en çarpıcı anı yakalar
                  </h3>
                  <p className="text-zinc-400 text-lg leading-relaxed">
                    Transkripti satır satır okumana gerek yok. Klipster konuşmayı analiz eder,
                    en ilgi çekici anları saniyeler içinde tespit eder ve öncelik sırasına göre listeler.
                  </p>
                  <div className="mt-auto flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-2 group-hover:translate-y-0">
                    <span className="text-xs font-mono text-orange-500">TÜMÜNÜ KEŞFET</span>
                    <ArrowRight className="w-4 h-4 text-orange-500" />
                  </div>
                </div>
                <div
                  className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none"
                  style={{ background: "radial-gradient(circle at top right, #f97316, transparent 70%)" }}
                />
              </div>

              {/* İlk ikincil kart daha genis */}
              <div className="lg:col-span-2 group relative overflow-hidden p-8 border border-white/10 bg-black hover:border-white/20 transition-all rounded-xl">
                <div className="relative z-10 flex flex-col h-full">
                  {(() => {
                    const PrimaryIcon = BENTO_SECONDARY[0].icon;
                    return (
                      <div className={`mb-4 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 w-fit ${BENTO_SECONDARY[0].color}`}>
                        <PrimaryIcon className="w-6 h-6" />
                      </div>
                    );
                  })()}
                  <h3 className="text-2xl font-semibold text-white font-display mb-2">{BENTO_SECONDARY[0].title}</h3>
                  <p className="text-zinc-400">{BENTO_SECONDARY[0].desc}</p>
                </div>
                <div
                  className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none"
                  style={{ background: "radial-gradient(circle at top right, #60a5fa, transparent 70%)" }}
                />
              </div>

              {/* Kalan iki kucuk kart */}
              {BENTO_SECONDARY.slice(1).map((f) => (
                <div
                  key={f.title}
                  className="group relative overflow-hidden p-8 border border-white/10 bg-black hover:border-white/20 transition-all rounded-xl"
                >
                  <div className="relative z-10">
                    <div className={`mb-4 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 w-fit ${f.color}`}>
                      <f.icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-semibold text-white font-display mb-2">{f.title}</h3>
                    <p className="text-sm text-zinc-400">{f.desc}</p>
                  </div>
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
                  className="bg-black border border-white/10 hover:border-white/20 transition-all rounded-2xl p-8"
                >
                  <p.icon className="h-5 w-5 text-orange-500" />
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
                  <span className="font-mono text-sm text-orange-500">{s.n}</span>
                  <h3 className="font-semibold text-lg mt-3 text-white">{s.title}</h3>
                  <p className="mt-2 text-sm text-zinc-400 leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Marka bandı */}
        <div className="w-full bg-orange-500 py-20 px-6">
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
                  <th className="text-center font-semibold px-6 py-4 text-orange-500">Klipster</th>
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
                          <Check className="h-4 w-4 text-orange-500 inline" />
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
              Viral anın <span className="text-orange-500">videonun içinde</span> bekliyor.
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
              <div className="w-5 h-5 bg-orange-500 rounded-sm rotate-45" />
              <span className="text-2xl font-bold font-display tracking-tight">Klipster</span>
            </div>
            <p className="text-zinc-500 max-w-xs leading-relaxed">
              İçerik üreticiler için sıfırdan tasarlanan yapay zeka klip stüdyosu.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-orange-500 uppercase tracking-widest mb-6">Ürün</h4>
            <ul className="space-y-4 text-zinc-400 text-sm">
              <li><a href="#ozellikler" className="hover:text-white transition-colors">Özellikler</a></li>
              <li><a href="#nasil-calisir" className="hover:text-white transition-colors">Nasıl Çalışır</a></li>
              <li><a href="#fiyatlandirma" className="hover:text-white transition-colors">Fiyatlandırma</a></li>
              <li><a href="#karsilastirma" className="hover:text-white transition-colors">Karşılaştırma</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-orange-500 uppercase tracking-widest mb-6">Hesap</h4>
            <ul className="space-y-4 text-zinc-400 text-sm">
              <li><Link href="/giris" className="hover:text-white transition-colors">Giriş Yap</Link></li>
              <li><Link href="/kayit" className="hover:text-white transition-colors">Üye Ol</Link></li>
              <li><Link href="/app" className="hover:text-white transition-colors">Panel</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-orange-500 uppercase tracking-widest mb-6">Yasal</h4>
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
