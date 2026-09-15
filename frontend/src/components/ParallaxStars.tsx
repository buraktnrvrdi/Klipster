"use client";

import { useEffect, useState } from "react";

// Klipster arka planı için parallax piksel-yıldız katmanları. Her katman
// yüzlerce yıldızı tek bir elemanın box-shadow'una gömerek (DOM'da binlerce
// ayrı node oluşturmadan) verimli şekilde çiziyor; üç katman farklı
// boyut/hızda kayarak derinlik hissi veriyor. Kayma sırasında "kesik"
// görünmemesi için her katmanın 2000px altında aynı yıldızların bir kopyası
// duruyor - şerit yukarı kaydıkça alttaki kopya sorunsuzca devreye giriyor.
//
// Yıldızlar Math.random() ile üretildiği için sunucu ve istemcide farklı
// çıkar (hydration mismatch olur); bu yüzden ilk render'da hiçbir şey
// çizmiyor, mount olduktan SONRA (useEffect içinde) üretip state'e yazıyoruz.

function generateBoxShadows(count: number): string {
  const stars: string[] = [];
  for (let i = 0; i < count; i++) {
    const x = Math.floor(Math.random() * 2000);
    const y = Math.floor(Math.random() * 2000);
    stars.push(`${x}px ${y}px #FFF`);
  }
  return stars.join(", ");
}

type StarLayers = { small: string; medium: string; big: string };

export default function ParallaxStars({ speed = 1 }: { speed?: number }) {
  const [layers, setLayers] = useState<StarLayers | null>(null);

  useEffect(() => {
    setLayers({
      small: generateBoxShadows(700),
      medium: generateBoxShadows(200),
      big: generateBoxShadows(100),
    });
  }, []);

  if (!layers) return null;

  return (
    <>
      <div
        className="absolute left-0 top-0 w-[1px] h-[1px] bg-transparent"
        style={{ boxShadow: layers.small, animation: `animStar ${50 / speed}s linear infinite` }}
      >
        <div className="absolute top-[2000px] w-[1px] h-[1px] bg-transparent" style={{ boxShadow: layers.small }} />
      </div>
      <div
        className="absolute left-0 top-0 w-[2px] h-[2px] bg-transparent"
        style={{ boxShadow: layers.medium, animation: `animStar ${100 / speed}s linear infinite` }}
      >
        <div className="absolute top-[2000px] w-[2px] h-[2px] bg-transparent" style={{ boxShadow: layers.medium }} />
      </div>
      <div
        className="absolute left-0 top-0 w-[3px] h-[3px] bg-transparent"
        style={{ boxShadow: layers.big, animation: `animStar ${150 / speed}s linear infinite` }}
      >
        <div className="absolute top-[2000px] w-[3px] h-[3px] bg-transparent" style={{ boxShadow: layers.big }} />
      </div>
    </>
  );
}
