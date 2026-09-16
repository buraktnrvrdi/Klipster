"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Check, Sparkles, Zap, Building2 } from "lucide-react";

type Plan = {
  id: "ucretsiz" | "yaratici" | "ajans";
  name: string;
  icon: typeof Sparkles;
  price: number | null; // null = "İletişime geç"
  priceLabel: string;
  tagline: string;
  monthlyVideoLimit: number | null; // null = sınırsız
  features: string[];
  cta: string;
  highlighted?: boolean;
};

const PLANS: Plan[] = [
  {
    id: "ucretsiz",
    name: "Başlangıç",
    icon: Sparkles,
    price: 0,
    priceLabel: "Ücretsiz",
    tagline: "Denemek için.",
    monthlyVideoLimit: 2,
    features: ["Ayda 2 video", "Video başına 4 klip", "Standart altyazı"],
    cta: "Ücretsiz Başla",
  },
  {
    id: "yaratici",
    name: "Yaratıcı",
    icon: Zap,
    price: 19,
    priceLabel: "$19",
    tagline: "İçerik üreticiler için.",
    monthlyVideoLimit: 20,
    features: ["Ayda 20 video", "Video başına 6 klip", "Gelişmiş altyazı stilleri", "Dolgu kelime temizliği"],
    cta: "Yaratıcı'ya Geç",
    highlighted: true,
  },
  {
    id: "ajans",
    name: "Ajans",
    icon: Building2,
    price: 49,
    priceLabel: "$49",
    tagline: "Ekipler için.",
    monthlyVideoLimit: null,
    features: ["Sınırsız video", "Çoklu kullanıcı", "Öncelikli destek"],
    cta: "İletişime Geç",
  },
];

function recommendPlan(videoCount: number): Plan["id"] {
  if (videoCount <= 2) return "ucretsiz";
  if (videoCount <= 20) return "yaratici";
  return "ajans";
}

export default function PricingCalculator() {
  const [videoCount, setVideoCount] = useState(8);

  const recommendedId = useMemo(() => recommendPlan(videoCount), [videoCount]);
  const recommendedPlan = PLANS.find((p) => p.id === recommendedId)!;
  const perVideoCost =
    recommendedPlan.price && recommendedPlan.price > 0
      ? (recommendedPlan.price / Math.max(videoCount, 1)).toFixed(0)
      : null;

  return (
    <section id="fiyatlandirma" className="relative py-24 px-6 overflow-hidden">
      {/* "Perde" (curtain) arka plan - katmanli gradyan isiklar */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-red-600/15 rounded-full blur-[140px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[400px] bg-amber-500/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/40 to-black" />
      </div>

      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-14"
        >
          <h2 className="text-4xl md:text-5xl font-semibold text-white font-display mb-4">
            Basit, şeffaf fiyatlandırma
          </h2>
          <p className="text-zinc-400">Gizli ücret yok, sürpriz fatura yok — ihtiyacın kadar öde.</p>
        </motion.div>

        {/* Kullanim hesaplayici */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="max-w-2xl mx-auto mb-16 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 sm:p-8"
        >
          <div className="flex items-center justify-between gap-4 flex-wrap mb-2">
            <label htmlFor="video-slider" className="text-sm font-medium text-zinc-300">
              Ayda kaç video işlemeyi planlıyorsun?
            </label>
            <span className="font-display text-2xl font-bold text-red-500 tabular-nums">
              {videoCount} video
            </span>
          </div>
          <input
            id="video-slider"
            type="range"
            min={1}
            max={60}
            step={1}
            value={videoCount}
            onChange={(e) => setVideoCount(Number(e.target.value))}
            className="w-full mt-4 accent-red-500 cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-zinc-600 mt-1 font-mono">
            <span>1</span>
            <span>60+</span>
          </div>

          <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-xs uppercase tracking-widest text-zinc-500">Önerilen plan</p>
              <p className="text-lg font-semibold text-white mt-1">{recommendedPlan.name}</p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-widest text-zinc-500">Tahmini aylık maliyet</p>
              <p className="text-lg font-semibold text-red-500 mt-1">
                {recommendedPlan.priceLabel}
                {perVideoCost && <span className="text-zinc-500 font-normal text-sm"> · video başına ~${perVideoCost}</span>}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Fiyat kartlari */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {PLANS.map((plan, i) => {
            const isRecommended = plan.id === recommendedId;
            return (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.5, delay: 0.1 * i }}
                whileHover={{ y: -4 }}
                className={`relative flex flex-col p-8 rounded-xl backdrop-blur-xl transition-colors duration-300 ${
                  plan.highlighted
                    ? "border border-red-500 bg-white/[0.06] shadow-[0_0_40px_rgba(239,68,68,0.18)] md:scale-105 z-10"
                    : "border border-white/10 bg-white/[0.03] hover:border-white/20"
                } ${isRecommended && !plan.highlighted ? "border-red-500/50" : ""}`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-red-500 text-black text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full">
                    Popüler
                  </div>
                )}
                {isRecommended && (
                  <div
                    className={`absolute -top-3 ${plan.highlighted ? "right-6" : "left-1/2 -translate-x-1/2"} bg-white text-black text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full`}
                  >
                    Sana uygun
                  </div>
                )}

                <div className={`mb-4 inline-flex p-2.5 rounded-lg bg-white/5 border border-white/10 w-fit ${plan.highlighted ? "text-red-500" : "text-zinc-400"}`}>
                  <plan.icon className="w-5 h-5" />
                </div>

                <h3 className="text-xl font-bold font-display mb-1 text-white">{plan.name}</h3>
                <p className="text-zinc-500 text-sm mb-6 h-10">{plan.tagline}</p>

                <div className="mb-8 flex items-baseline gap-1">
                  {plan.price === 0 ? (
                    <span className="text-4xl font-bold text-white">Ücretsiz</span>
                  ) : (
                    <>
                      <span className="text-4xl font-bold text-white">{plan.priceLabel}</span>
                      <span className="text-zinc-500 text-sm">/ay</span>
                    </>
                  )}
                </div>

                <ul className="space-y-3.5 mb-8 flex-1">
                  {plan.features.map((item) => (
                    <li key={item} className="flex items-center gap-3 text-sm text-zinc-300">
                      <Check className={`h-4 w-4 shrink-0 ${plan.highlighted ? "text-red-500" : "text-zinc-500"}`} />
                      {item}
                    </li>
                  ))}
                </ul>

                <Link
                  href="/kayit"
                  className={`w-full text-center py-3 px-4 rounded-lg text-sm font-bold uppercase tracking-wider transition-all ${
                    plan.highlighted
                      ? "bg-red-500 hover:bg-red-600 text-black"
                      : "bg-white/5 hover:bg-white/10 text-white border border-white/10"
                  }`}
                >
                  {plan.cta}
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
