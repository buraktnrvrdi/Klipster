"use client";

import { useEffect, useState } from "react";

const CLIPS = [
  {
    caption: "bu gerçekten inanılmaz bir an",
    highlight: "inanılmaz",
    tag: "@icerik_ureticisi",
    time: "00:24",
    from: "#141414",
    to: "#3a1313",
  },
  {
    caption: "kimse bunu beklemiyordu ama",
    highlight: "beklemiyordu",
    tag: "@podcast_tr",
    time: "00:41",
    from: "#12141c",
    to: "#241111",
  },
  {
    caption: "işte bu yüzden fark yaratıyor",
    highlight: "fark yaratıyor",
    tag: "@roportaj_kanali",
    time: "00:17",
    from: "#151313",
    to: "#220d0d",
  },
];

const DURATION = 4000;

export default function PhoneShowcase() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % CLIPS.length);
    }, DURATION);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="relative">
      {/* soft ambient glow, static — no bouncing */}
      <div
        className="absolute inset-0 -z-10 rounded-full blur-[90px] opacity-50"
        style={{
          background:
            "radial-gradient(circle, rgba(239,68,68,0.35), transparent 70%)",
        }}
      />

      <div className="relative w-72 aspect-[9/19.5] rounded-[2.75rem] border-[10px] border-neutral-900 bg-neutral-900 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.35)] overflow-hidden">
        {/* stacked crossfading backgrounds */}
        {CLIPS.map((clip, i) => (
          <div
            key={i}
            className="absolute inset-0 transition-opacity ease-in-out"
            style={{
              background: `linear-gradient(160deg, ${clip.from}, ${clip.to})`,
              opacity: i === index ? 1 : 0,
              transitionDuration: "1200ms",
            }}
          />
        ))}

        {/* subtle vignette for depth */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/20" />
        <div className="absolute inset-0 shadow-[inset_0_0_60px_rgba(0,0,0,0.35)]" />

        {/* dynamic island */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-20 h-5 bg-black rounded-full z-20" />

        {/* progress bar */}
        <div className="absolute top-7 left-4 right-4 flex gap-1 z-20">
          {CLIPS.map((_, i) => (
            <div
              key={i}
              className="h-[3px] flex-1 bg-white/25 rounded-full overflow-hidden"
            >
              <div
                className="h-full bg-white rounded-full"
                style={{
                  width: i < index ? "100%" : i === index ? "100%" : "0%",
                  transitionProperty: "width",
                  transitionDuration: i === index ? `${DURATION}ms` : "0ms",
                  transitionTimingFunction: "linear",
                }}
              />
            </div>
          ))}
        </div>

        {/* play icon */}
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="h-14 w-14 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/10">
            <div className="h-0 w-0 border-y-[8px] border-y-transparent border-l-[13px] border-l-white/90 ml-1" />
          </div>
        </div>

        {/* stacked crossfading captions */}
        <div className="absolute bottom-24 left-4 right-4 z-20">
          {CLIPS.map((clip, i) => (
            <div
              key={i}
              className="absolute inset-x-0 bottom-0 transition-all ease-in-out"
              style={{
                opacity: i === index ? 1 : 0,
                transform: i === index ? "translateY(0)" : "translateY(6px)",
                transitionDuration: "700ms",
              }}
            >
              <div className="bg-black/45 backdrop-blur-md rounded-lg px-4 py-2.5 border border-white/10">
                <p className="text-white text-[15px] font-medium text-center leading-snug tracking-tight">
                  {clip.caption.split(clip.highlight)[0]}
                  <span className="text-red-400">{clip.highlight}</span>
                  {clip.caption.split(clip.highlight)[1]}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* footer meta */}
        <div className="absolute bottom-6 left-4 right-4 flex items-center justify-between text-white/50 text-[11px] font-medium z-20">
          {CLIPS.map((clip, i) => (
            <span
              key={i}
              className="absolute inset-x-0 flex items-center justify-between transition-opacity"
              style={{
                opacity: i === index ? 1 : 0,
                transitionDuration: "700ms",
              }}
            >
              <span>{clip.tag}</span>
              <span>{clip.time}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
