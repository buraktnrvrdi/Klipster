"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronDown, Mail } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const FAQ: { q: string; a: string }[] = [
  {
    q: "Kredi sistemi nasıl çalışıyor?",
    a: "Her video, süresine ve seçtiğin klip sayısına göre bir miktar kredi harcar - uzun bir video ve çok sayıda klip, kısa bir videodan daha fazla kredi tüketir. Krediler her ayın başında planına göre yenilenir, kullanılmayan krediler bir sonraki aya devretmez. Bir video işlenirken hata oluşursa harcanan kredi otomatik olarak iade edilir (o işin kredisi aylık toplamına dahil edilmez).",
  },
  {
    q: "Hangi video formatlarını yükleyebilirim?",
    a: "Standart video formatlarının (mp4, mov, mkv gibi) çoğunu destekliyoruz. Kaynak videonun yatay, dikey ya da kare olması fark etmez - klip çıktısını istediğin en-boy oranında (9:16, 4:5 veya 1:1) alabilirsin.",
  },
  {
    q: "Videom ne kadar sürede işleniyor?",
    a: "Süre, videonun uzunluğuna ve o an sunucudaki yoğunluğa göre değişir; genellikle birkaç dakika sürer. İşlem tamamlandığında video geçmişinde durumunu görebilirsin.",
  },
  {
    q: "Verilerim ve videolarım güvende mi?",
    a: "Şifren geri döndürülemez şekilde şifrelenerek saklanır, oturumların 30 gün sonra otomatik olarak sona erer. Videoların sadece senin (veya ekibindeysen ekibinin) erişebileceği şekilde saklanır. Detaylar için gizlilik politikamıza bakabilirsin.",
  },
  {
    q: "Ücretli bir plana nasıl geçebilirim?",
    a: "Gerçek ödeme altyapımız şu an geliştirme aşamasında - yakında eklenecek. Şimdilik ücretsiz planla platformu deneyimleyebilirsin, ödeme sistemi devreye girdiğinde tüm kullanıcılara duyuracağız.",
  },
  {
    q: "Ekip/Ajans özelliği ne işe yarar?",
    a: "Bir ekip oluşturduğunda, ekibe davet ettiğin kişiler senin plan haklarını (kredi limiti, klip özelleştirme) paylaşır ve yüklenen tüm videoları birlikte görebilirsiniz - ajans veya küçük bir içerik ekibiyle çalışıyorsan bu özellik tam senlik.",
  },
  {
    q: "Hesabımı nasıl silerim?",
    a: "Profilim sayfasındaki \"Hesabımı sil\" bölümünden hesabını ve tüm verilerini (video/klip dosyaların dahil) kalıcı olarak silebilirsin. Bu işlem geri alınamaz.",
  },
];

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
      >
        <span className="text-sm font-medium text-zinc-200">{q}</span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-zinc-500 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <p className="px-5 pb-4 text-sm leading-relaxed text-zinc-400">{a}</p>
      )}
    </div>
  );
}

export default function IletisimPage() {
  return (
    <main className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#160b02] to-black" />
        <ParallaxStars speed={0.4} />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Logo className="h-9" />
          </Link>
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Ana sayfa
          </Link>
        </div>
      </header>

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-16">
        <h1 className="font-display text-3xl font-semibold tracking-tight">İletişim &amp; Sık Sorulan Sorular</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Bir sorunla mı karşılaştın, yoksa aklına bir öneri mi geldi? Aşağıdan bize ulaşabilirsin.
        </p>

        <a
          href="mailto:brightnotedestek@gmail.com"
          className="mt-6 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl px-6 py-5 hover:border-orange-500/40 transition-colors w-fit"
        >
          <div className="h-10 w-10 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center shrink-0">
            <Mail className="h-4 w-4 text-orange-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-zinc-200">brightnotedestek@gmail.com</p>
            <p className="text-xs text-zinc-500">Genelde 1-2 iş günü içinde dönüş yapıyoruz</p>
          </div>
        </a>

        <h2 className="mt-14 font-display text-xl font-semibold">Sık Sorulan Sorular</h2>
        <div className="mt-5 flex flex-col gap-2.5">
          {FAQ.map((item) => (
            <FaqItem key={item.q} q={item.q} a={item.a} />
          ))}
        </div>
      </div>
    </main>
  );
}
