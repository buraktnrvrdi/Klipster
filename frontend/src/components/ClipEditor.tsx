"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Check,
  Play,
  Pause,
  Loader2,
  Palette,
  Save,
  Wand2,
  AlignCenter,
  Monitor,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Clip = {
  title: string;
  reason: string;
  url: string;
  cover_url: string | null;
  score?: number | null;
  start?: number;
  end?: number;
  subtitles_en_url?: string | null;
  manual?: boolean;
  style?: string;
  subtitle_color?: string;
  subtitle_position?: string;
  aspect?: string;
  subtitle_animation?: string;
  highlight_color?: string;
};

type JobDetail = {
  job_id: string;
  status: string;
  clips: Clip[];
  style?: string;
  subtitle_color?: string;
  subtitle_position?: string;
  aspect?: string;
  subtitle_animation?: string;
  highlight_color?: string;
};

type RenderOptions = {
  aspects: { id: string; label: string }[];
  positions: { id: string; label: string }[];
  colors: { id: string; label: string; hex: string }[];
  animations: { id: string; label: string }[];
  credits: { base: number; per_clip: number };
};

const FALLBACK_STYLES: Record<string, string> = {
  klasik: "Klasik",
  vurgu: "Vurgulu (enerjik)",
  minimal: "Minimal",
  kalin: "Kalın (TikTok tarzı)",
  editorial: "Editöryel (dergi tarzı)",
  vintage: "Vintage (retro)",
};

const FALLBACK_RENDER_OPTIONS: RenderOptions = {
  aspects: [
    { id: "9:16", label: "Dikey (9:16)" },
    { id: "4:5", label: "Dikey (4:5)" },
    { id: "1:1", label: "Kare (1:1)" },
  ],
  positions: [
    { id: "alt", label: "Alt" },
    { id: "orta", label: "Orta" },
    { id: "ust", label: "Üst" },
  ],
  colors: [
    { id: "beyaz", label: "Beyaz", hex: "#FFFFFF" },
    { id: "turuncu", label: "Turuncu", hex: "#F97316" },
    { id: "sari", label: "Sarı", hex: "#FACC15" },
    { id: "yesil", label: "Yeşil", hex: "#22C55E" },
    { id: "mavi", label: "Mavi", hex: "#3B82F6" },
    { id: "pembe", label: "Pembe", hex: "#EC4899" },
    { id: "kirmizi", label: "Kırmızı", hex: "#EF4444" },
  ],
  animations: [
    { id: "statik", label: "Statik (klasik)" },
    { id: "karaoke", label: "Kelime vurgulu (karaoke)" },
    { id: "pop", label: "Zıplayan (pop)" },
    { id: "daktilo", label: "Daktilo (harf harf)" },
    { id: "kayan", label: "Kayarak giren" },
  ],
  credits: { base: 4, per_clip: 2 },
};

const ASPECT_CLASS: Record<string, string> = {
  "9:16": "aspect-[9/16]",
  "4:5": "aspect-[4/5]",
  "1:1": "aspect-square",
};

type Word = { start: number; end: number; word: string };
type StylePreset = { label: string; chunk_size: number };

// backend/app/services/video.py STYLE_PRESETS'teki chunk_size degerleriyle
// birebir ayni - /api/caption-style-presets cekilemezse bu kullanilir.
const FALLBACK_STYLE_PRESETS: Record<string, StylePreset> = {
  klasik: { label: "Klasik", chunk_size: 4 },
  vurgu: { label: "Vurgulu (enerjik)", chunk_size: 2 },
  minimal: { label: "Minimal", chunk_size: 5 },
  kalin: { label: "Kalın (TikTok tarzı)", chunk_size: 2 },
  editorial: { label: "Editöryel (dergi tarzı)", chunk_size: 6 },
  vintage: { label: "Vintage (retro)", chunk_size: 3 },
};

/**
 * Video oynarken o an gosterilmesi gereken altyazi grubunu (chunk) bulur.
 * backend/app/services/video.py generate_ass() ile AYNI gruplama/zamanlama
 * mantigini kullanir (bkz. chunk_size'a gore gruplama, karaoke icin kelime
 * bazli w_start/w_end penceresi) - boylece editordeki onizleme, klip
 * yeniden uretildiginde yakilacak gercek altyaziyla tutarli olur.
 */
function getActiveCaption(
  words: Word[],
  chunkSize: number,
  rangeStart: number,
  rangeEnd: number,
  t: number,
  animation: string
): { words: Word[]; activeIndex: number; typedText?: string; chunkStart?: number } | null {
  const inRange = words.filter((w) => w.start >= rangeStart - 0.01 && w.start < rangeEnd);
  for (let i = 0; i < inRange.length; i += chunkSize) {
    const group = inRange.slice(i, i + chunkSize);
    if (group.length === 0) continue;
    // "karaoke" ve "pop" ayni pencereleme mantigini kullanir - ikisi de
    // grup boyunca hepsi gorunurken, o an konusulan TEK kelimeyi sirayla
    // vurgular (karaoke renkle, pop olcek/zipla ile) - bkz. backend video.py.
    if (animation === "karaoke" || animation === "pop") {
      const chunkEnd = group[group.length - 1].end;
      for (let j = 0; j < group.length; j++) {
        const wStart = group[j].start;
        let wEnd = j + 1 < group.length ? group[j + 1].start : chunkEnd;
        if (wEnd <= wStart) wEnd = Math.max(group[j].end, wStart + 0.05);
        if (t >= wStart && t < wEnd) {
          return { words: group, activeIndex: j, chunkStart: group[0].start };
        }
      }
    } else {
      const groupStart = group[0].start;
      const groupEnd = group[group.length - 1].end;
      if (t >= groupStart && t < groupEnd) {
        if (animation === "daktilo") {
          // backend generate_ass'teki daktilo adimlamasinin basitlestirilmis
          // (surekli/interpolasyonlu) onizleme karsiligi - gecen sureye gore
          // kac karakterin gosterilecegini hesaplar.
          const fullText = group.map((w) => w.word).join("").trim();
          const totalDur = Math.max(groupEnd - groupStart, 0.01);
          const frac = Math.min(1, Math.max(0, (t - groupStart) / totalDur));
          const charsShown = Math.max(1, Math.round(frac * fullText.length));
          return {
            words: group,
            activeIndex: -1,
            typedText: fullText.slice(0, charsShown),
            chunkStart: groupStart,
          };
        }
        return { words: group, activeIndex: -1, chunkStart: groupStart };
      }
    }
  }
  return null;
}

// Backend'deki (video.py) karaoke vurgu rengiyle birebir ayni - onizlemenin
// gercek render ile tutarli gorunmesi icin.
const KARAOKE_HIGHLIGHT = "#FFEB3B";

const SAMPLE_WORDS = ["Bu", "altyazı", "stili", "böyle", "görünür"];

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

function formatTime(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
}

/**
 * Her altyazi stilinin gercek render'daki gorunumunu (backend/app/services/video.py
 * icindeki STYLE_PRESETS'in ASS style satirlarindan cikarilan font/kalinlik/kontur
 * ozellikleri) yaklasik olarak CSS'e ceviren onizleme stili. Renk her zaman
 * kullanicinin sectigi subtitle_color ile ezilir (backend'de de boyle calisir),
 * bu yuzden burada da secili renk kullanilir.
 */
function styleSampleCss(key: string, color: string): CSSProperties {
  const base: CSSProperties = {
    color,
    fontFamily: "Arial, Helvetica, sans-serif",
    fontWeight: 700,
    fontSize: "0.95rem",
    letterSpacing: "0",
    textShadow:
      "0 0 3px #000, 1px 1px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000",
  };
  switch (key) {
    case "vurgu":
      return {
        ...base,
        fontWeight: 800,
        fontSize: "1.05rem",
        textShadow: "0 0 6px rgba(0,0,0,.95), 2px 2px 0 #000, -2px -2px 0 #000",
      };
    case "minimal":
      return {
        color,
        fontFamily: "Arial, Helvetica, sans-serif",
        fontWeight: 400,
        fontSize: "0.8rem",
        letterSpacing: "0.03em",
        textShadow: "0 1px 2px rgba(0,0,0,.6)",
        background: "rgba(0,0,0,0.45)",
        padding: "2px 8px",
        borderRadius: "6px",
      };
    case "kalin":
      return {
        ...base,
        fontWeight: 900,
        fontSize: "1.15rem",
        textShadow:
          "0 0 4px #000, 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 0 3px 6px rgba(0,0,0,.8)",
      };
    case "editorial":
      return {
        color,
        fontFamily: "Georgia, 'Times New Roman', serif",
        fontWeight: 300,
        fontSize: "0.9rem",
        letterSpacing: "0.12em",
        textShadow: "0 1px 3px rgba(0,0,0,.5)",
      };
    case "vintage":
      return {
        color,
        fontFamily: "Georgia, 'Times New Roman', serif",
        fontWeight: 500,
        fontSize: "0.9rem",
        letterSpacing: "0.02em",
        textShadow: "1px 1px 0 #3b0f0f, -1px -1px 0 #3b0f0f, 0 2px 4px rgba(0,0,0,.5)",
      };
    case "klasik":
    default:
      return base;
  }
}

/**
 * Kenar cubugundaki stil karti onizlemesinde altyazi animasyonunun nasil
 * goruneceginin dogru (ama gercek yakma islemiyle ayni olmasi gerekmeyen)
 * bir CSS onizlemesi. "tick", cagiran bilesenin duzenli araliklarla
 * artirdigi bir sayac - pop/daktilo/kayan icin dongusel bir onizleme
 * yaratmak amaciyla kullanilir (statik/karaoke icin degismedi).
 */
function renderSampleWords(animation: string, tick = 0, highlightColor: string = KARAOKE_HIGHLIGHT): ReactNode {
  if (animation === "karaoke") {
    return SAMPLE_WORDS.map((w, i) => (
      <span key={i} style={i === 2 ? { color: highlightColor, fontWeight: 900 } : undefined}>
        {w}
        {i < SAMPLE_WORDS.length - 1 ? " " : ""}
      </span>
    ));
  }
  if (animation === "pop") {
    const activeIdx = tick % SAMPLE_WORDS.length;
    return SAMPLE_WORDS.map((w, i) => (
      <span
        key={`${i}-${i === activeIdx ? tick : "idle"}`}
        className={i === activeIdx ? "cap-pop-word" : undefined}
        style={{
          display: "inline-block",
          fontWeight: i === activeIdx ? 900 : undefined,
          color: i === activeIdx ? highlightColor : undefined,
        }}
      >
        {w}
        {i < SAMPLE_WORDS.length - 1 ? " " : ""}
      </span>
    ));
  }
  if (animation === "daktilo") {
    const fullText = SAMPLE_WORDS.join(" ");
    const cycle = fullText.length + 8;
    const charsShown = Math.min(fullText.length, tick % cycle);
    return (
      <span>
        {fullText.slice(0, charsShown)}
        <span className="cap-cursor">|</span>
      </span>
    );
  }
  if (animation === "kayan") {
    const cycleTick = tick - (tick % 6);
    return (
      <span key={cycleTick} className="cap-slide-chunk" style={{ display: "inline-block" }}>
        {SAMPLE_WORDS.join(" ")}
      </span>
    );
  }
  return SAMPLE_WORDS.join(" ");
}

function EditorTimeline({
  duration,
  start,
  end,
  currentTime,
  onRangeChange,
  onSeek,
}: {
  duration: number;
  start: number;
  end: number;
  currentTime: number;
  onRangeChange: (start: number, end: number, movedHandle: "start" | "end") => void;
  onSeek: (t: number) => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<"start" | "end" | "playhead" | null>(null);
  const rangeRef = useRef({ start, end });
  useEffect(() => {
    rangeRef.current = { start, end };
  }, [start, end]);

  const timeFromClientX = useCallback(
    (clientX: number) => {
      const track = trackRef.current;
      if (!track || duration === 0) return 0;
      const rect = track.getBoundingClientRect();
      const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
      return ratio * duration;
    },
    [duration]
  );

  useEffect(() => {
    if (!dragging) return;
    function handleMove(e: PointerEvent) {
      const t = timeFromClientX(e.clientX);
      const { start: curStart, end: curEnd } = rangeRef.current;
      if (dragging === "start") {
        onRangeChange(Math.max(0, Math.min(t, curEnd - 1)), curEnd, "start");
      } else if (dragging === "end") {
        onRangeChange(curStart, Math.min(duration || Infinity, Math.max(t, curStart + 1)), "end");
      } else {
        onSeek(Math.min(duration || Infinity, Math.max(0, t)));
      }
    }
    function handleUp() {
      setDragging(null);
    }
    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp);
    return () => {
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };
  }, [dragging, duration, onRangeChange, onSeek, timeFromClientX]);

  const startPct = duration ? (start / duration) * 100 : 0;
  const endPct = duration ? (end / duration) * 100 : 100;
  const playPct = duration ? (Math.min(currentTime, duration) / duration) * 100 : 0;

  return (
    <div className="w-full flex flex-col gap-2">
      <div
        ref={trackRef}
        onPointerDown={(e) => {
          e.preventDefault();
          setDragging("playhead");
          onSeek(timeFromClientX(e.clientX));
        }}
        className="relative h-12 rounded-lg bg-white/10 select-none touch-none cursor-pointer overflow-hidden"
      >
        <div
          className="absolute inset-y-0 bg-red-500/20 border-y-2 border-red-500/60"
          style={{ left: `${startPct}%`, right: `${100 - endPct}%` }}
        />
        <div
          className="absolute inset-y-0 w-0.5 bg-white shadow-[0_0_6px_rgba(255,255,255,.8)] pointer-events-none"
          style={{ left: `${playPct}%` }}
        />
        <div
          onPointerDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setDragging("start");
          }}
          className="absolute inset-y-0 -ml-2.5 w-5 rounded-md bg-red-500 cursor-ew-resize touch-none shadow-lg flex items-center justify-center"
          style={{ left: `${startPct}%` }}
        >
          <div className="h-5 w-0.5 bg-black/40 rounded-full" />
        </div>
        <div
          onPointerDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setDragging("end");
          }}
          className="absolute inset-y-0 -ml-2.5 w-5 rounded-md bg-red-500 cursor-ew-resize touch-none shadow-lg flex items-center justify-center"
          style={{ left: `${endPct}%` }}
        >
          <div className="h-5 w-0.5 bg-black/40 rounded-full" />
        </div>
      </div>
      <div className="flex justify-between text-[11px] text-zinc-500">
        <span>{formatTime(start)}</span>
        <span className="text-zinc-300 font-medium">{formatTime(end - start)} klip süresi</span>
        <span>{formatTime(end)}</span>
      </div>
    </div>
  );
}

export default function ClipEditor({ jobId, clipIndex }: { jobId: string; clipIndex: number }) {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);

  const [token, setToken] = useState<string | null>(null);
  const [clip, setClip] = useState<Clip | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [styles, setStyles] = useState<Record<string, string>>(FALLBACK_STYLES);
  const [renderOptions, setRenderOptions] = useState<RenderOptions>(FALLBACK_RENDER_OPTIONS);
  const [stylePresets, setStylePresets] = useState<Record<string, StylePreset>>(FALLBACK_STYLE_PRESETS);
  const [words, setWords] = useState<Word[]>([]);

  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [playing, setPlaying] = useState(false);

  const [clipStyle, setClipStyle] = useState("klasik");
  const [clipColor, setClipColor] = useState("#FFFFFF");
  const [clipPosition, setClipPosition] = useState("alt");
  const [clipAspect, setClipAspect] = useState("9:16");
  const [clipAnimation, setClipAnimation] = useState("statik");
  const [clipHighlightColor, setClipHighlightColor] = useState(KARAOKE_HIGHLIGHT);
  const [previewTick, setPreviewTick] = useState(0);

  // Kenar cubugundaki animasyon onizlemesini (pop/daktilo/kayan) donguye
  // sokan sayac - karaoke/statik icin gereksiz oldugundan sadece o modlarda
  // calisir, boylece gereksiz re-render yapilmaz.
  useEffect(() => {
    if (!(clipAnimation === "pop" || clipAnimation === "daktilo" || clipAnimation === "kayan")) return;
    const id = setInterval(() => setPreviewTick((n) => n + 1), 260);
    return () => clearInterval(id);
  }, [clipAnimation]);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("klipster_token");
    if (!t) {
      router.push("/giris");
      return;
    }
    setToken(t);
  }, [router]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setLoadError(null);
      try {
        const [jobRes, stylesRes, optsRes, presetsRes, wordsRes] = await Promise.all([
          fetch(`${API_URL}/api/jobs/${jobId}`, { headers: authHeaders(token as string) }),
          fetch(`${API_URL}/api/caption-styles`).catch(() => null),
          fetch(`${API_URL}/api/render-options`).catch(() => null),
          fetch(`${API_URL}/api/caption-style-presets`).catch(() => null),
          fetch(`${API_URL}/api/jobs/${jobId}/words`, { headers: authHeaders(token as string) }).catch(() => null),
        ]);
        if (!jobRes.ok) throw new Error("Video bulunamadı");
        const jobData: JobDetail = await jobRes.json();
        if (cancelled) return;

        if (stylesRes && stylesRes.ok) {
          const s = await stylesRes.json();
          if (s && Object.keys(s).length > 0 && !cancelled) setStyles(s);
        }
        if (optsRes && optsRes.ok) {
          const o = await optsRes.json();
          if (
            o &&
            o.aspects?.length &&
            o.positions?.length &&
            o.colors?.length &&
            o.animations?.length &&
            !cancelled
          ) {
            setRenderOptions(o);
          }
        }
        if (presetsRes && presetsRes.ok) {
          const p = await presetsRes.json();
          if (p && Object.keys(p).length > 0 && !cancelled) setStylePresets(p);
        }
        if (wordsRes && wordsRes.ok) {
          const w = await wordsRes.json();
          if (Array.isArray(w?.words) && !cancelled) setWords(w.words);
        }

        const c = jobData.clips?.[clipIndex];
        if (!c || c.start === undefined || c.end === undefined) {
          throw new Error("Klip bulunamadı");
        }
        setClip(c);
        setStart(c.start);
        setEnd(c.end);
        setClipStyle(c.style ?? jobData.style ?? "klasik");
        setClipColor(c.subtitle_color ?? jobData.subtitle_color ?? "#FFFFFF");
        setClipPosition(c.subtitle_position ?? jobData.subtitle_position ?? "alt");
        setClipAspect(c.aspect ?? jobData.aspect ?? "9:16");
        setClipAnimation(c.subtitle_animation ?? jobData.subtitle_animation ?? "statik");
        setClipHighlightColor(c.highlight_color ?? jobData.highlight_color ?? KARAOKE_HIGHLIGHT);
      } catch (e) {
        if (!cancelled) setLoadError(e instanceof Error ? e.message : "Yüklenemedi");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [token, jobId, clipIndex]);

  function togglePlay() {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) {
      if (v.currentTime < start || v.currentTime >= end) v.currentTime = start;
      v.play().catch(() => {});
    } else {
      v.pause();
    }
  }

  function handleRangeChange(nextStart: number, nextEnd: number, movedHandle: "start" | "end") {
    setStart(nextStart);
    setEnd(nextEnd);
    // Baslangic tutamagini suruklerken baslangic karesini, bitis tutamagini
    // suruklerken bitis karesini gostererek kullanicinin sectigi araligi
    // videonun kendisinde anlik gorebilmesini sagliyoruz.
    const seekTo = movedHandle === "start" ? nextStart : nextEnd;
    const v = videoRef.current;
    if (v) {
      if (!v.paused) v.pause();
      v.currentTime = seekTo;
    }
    setCurrentTime(seekTo);
  }

  function handleSeek(t: number) {
    setCurrentTime(t);
    if (videoRef.current) videoRef.current.currentTime = t;
  }

  async function handleSave() {
    if (!token) return;
    setSaving(true);
    setSaveError(null);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/${clipIndex}/retrim`, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({
          start,
          end,
          style: clipStyle,
          subtitle_color: clipColor,
          subtitle_position: clipPosition,
          aspect: clipAspect,
          subtitle_animation: clipAnimation,
          highlight_color: clipHighlightColor,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSaveError(data.detail || "Kaydedilemedi");
        return;
      }
      router.push(`/app?job=${jobId}`);
    } catch {
      setSaveError("Sunucuya ulaşılamadı");
    } finally {
      setSaving(false);
    }
  }

  if (!token) return null;

  const aspectClass = ASPECT_CLASS[clipAspect] || ASPECT_CLASS["9:16"];
  const canSave = !loading && !!clip && end - start >= 3;

  return (
    <main className="min-h-screen bg-black text-white flex flex-col">
      <header className="sticky top-0 z-20 shrink-0 flex items-center justify-between gap-3 border-b border-white/10 bg-black/70 backdrop-blur-xl px-4 sm:px-6 py-3">
        <div className="flex items-center gap-3 min-w-0">
          <button
            type="button"
            onClick={() => router.push(`/app?job=${jobId}`)}
            className="flex items-center gap-1.5 text-zinc-400 hover:text-white text-sm font-medium transition-colors shrink-0"
          >
            <ArrowLeft className="h-4 w-4" />
            Vazgeç
          </button>
          <div className="h-5 w-px bg-white/10 hidden sm:block" />
          <div className="min-w-0 hidden sm:block">
            <p className="text-sm font-medium text-white truncate max-w-[260px]">
              {clip?.title ?? "Klip Düzenleyici"}
            </p>
            <p className="text-[11px] text-zinc-500">Profesyonel Düzenleyici</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={!canSave || saving}
          className="flex items-center gap-1.5 bg-red-500 text-black px-5 py-2 rounded-full text-sm font-semibold hover:bg-red-600 transition disabled:opacity-40 shrink-0"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {saving ? "Kaydediliyor..." : "Kaydet ve Oluştur"}
        </button>
      </header>

      {saveError && (
        <div className="shrink-0 px-4 sm:px-6 pt-3">
          <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
            {saveError}
          </p>
        </div>
      )}

      {loadError ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
            {loadError}
          </p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col lg:flex-row">
          <aside className="w-full lg:w-72 shrink-0 border-b lg:border-b-0 lg:border-r border-white/10 bg-white/[0.02] p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-3">
              Altyazı Stili
            </h2>
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-2.5">
              {Object.entries(styles).map(([key, label]) => {
                const active = clipStyle === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setClipStyle(key)}
                    className={`text-left rounded-xl border p-2.5 transition-colors ${
                      active
                        ? "border-red-500 bg-red-500/10"
                        : "border-white/10 bg-black/30 hover:border-white/25"
                    }`}
                  >
                    <div className="relative rounded-lg bg-zinc-900 aspect-video overflow-hidden mb-2">
                      <div className="absolute inset-0 bg-gradient-to-b from-zinc-800 to-zinc-950" />
                      <div className="absolute inset-0 flex items-end justify-center px-2 pb-2">
                        <span
                          className="relative text-center leading-tight"
                          style={styleSampleCss(key, clipColor)}
                        >
                          {renderSampleWords(clipAnimation, previewTick, clipHighlightColor)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between gap-1">
                      <span
                        className={`text-xs font-medium ${active ? "text-red-300" : "text-zinc-300"}`}
                      >
                        {label}
                      </span>
                      {active && <Check className="h-3.5 w-3.5 text-red-400 shrink-0" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </aside>

          <section className="flex-1 flex flex-col items-center gap-5 p-4 lg:p-8">
            {loading ? (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="h-6 w-6 text-zinc-500 animate-spin" />
              </div>
            ) : clip ? (
              <>
                <div className="w-full max-w-sm mx-auto">
                  <div
                    className={`relative mx-auto rounded-2xl overflow-hidden bg-black border border-white/10 shadow-2xl ${aspectClass}`}
                  >
                    <video
                      ref={videoRef}
                      src={`${API_URL}/api/jobs/${jobId}/source?token=${encodeURIComponent(token)}`}
                      className="w-full h-full object-cover bg-black"
                      onLoadedMetadata={(e) => {
                        setDuration(e.currentTarget.duration);
                        e.currentTarget.currentTime = start;
                      }}
                      onTimeUpdate={(e) => {
                        const t = e.currentTarget.currentTime;
                        setCurrentTime(t);
                        if (!e.currentTarget.paused && t >= end) {
                          e.currentTarget.currentTime = start;
                        }
                      }}
                      onPlay={() => setPlaying(true)}
                      onPause={() => setPlaying(false)}
                      playsInline
                    />
                    {(() => {
                      const chunkSize = stylePresets[clipStyle]?.chunk_size ?? 4;
                      const active = getActiveCaption(words, chunkSize, start, end, currentTime, clipAnimation);
                      if (!active) return null;
                      const posClass =
                        clipPosition === "ust"
                          ? "top-[8%]"
                          : clipPosition === "orta"
                          ? "top-1/2 -translate-y-1/2"
                          : "bottom-[8%]";
                      const baseSpanStyle = { ...styleSampleCss(clipStyle, clipColor), fontSize: "1.15rem" };
                      let captionContent: ReactNode;
                      if (clipAnimation === "daktilo") {
                        // Daktilo: backend'de her adim ayri Dialogue satiri olarak
                        // biriken bir on-ek (prefix) gosterir - onizlemede de ayni
                        // sekilde typedText'i (kirpilmis metni) yaniyor imleçle gosteriyoruz.
                        captionContent = (
                          <>
                            {active.typedText}
                            <span className="cap-cursor">|</span>
                          </>
                        );
                      } else if (clipAnimation === "pop") {
                        // Pop: aktif kelime renk degil OLCEK (scale) ile vurgulanir -
                        // backend'deki \fscx/\fscy \t() gecisiyle tutarli.
                        captionContent = active.words.map((w, i) => (
                          <span
                            key={i}
                            className={i === active.activeIndex ? "cap-pop-word" : undefined}
                            style={{
                              display: "inline-block",
                              fontWeight: i === active.activeIndex ? 900 : undefined,
                              color: i === active.activeIndex ? clipHighlightColor : undefined,
                            }}
                          >
                            {w.word}
                            {i < active.words.length - 1 ? " " : ""}
                          </span>
                        ));
                      } else if (clipAnimation === "kayan") {
                        // Kayan: tum chunk, yeni chunk basladiginda asagidan/yukaridan
                        // kayarak oturur - chunkStart degistikce React key ile yeniden
                        // mount edilip animasyon tekrar tetiklenir.
                        captionContent = (
                          <span key={active.chunkStart} className="cap-slide-chunk" style={{ display: "inline-block" }}>
                            {active.words.map((w) => w.word).join(" ")}
                          </span>
                        );
                      } else {
                        // karaoke / statik
                        captionContent = active.words.map((w, i) => (
                          <span
                            key={i}
                            style={
                              i === active.activeIndex
                                ? { color: clipHighlightColor, fontWeight: 900, display: "inline-block", transform: "scale(1.12)" }
                                : undefined
                            }
                          >
                            {w.word}
                            {i < active.words.length - 1 ? " " : ""}
                          </span>
                        ));
                      }
                      return (
                        <div
                          className={`absolute left-0 right-0 px-4 flex justify-center pointer-events-none ${posClass}`}
                        >
                          <span className="text-center max-w-[92%] leading-snug" style={baseSpanStyle}>
                            {captionContent}
                          </span>
                        </div>
                      );
                    })()}
                    <button
                      type="button"
                      onClick={togglePlay}
                      className="absolute inset-0 flex items-center justify-center bg-black/0 hover:bg-black/20 transition-colors group"
                    >
                      <span
                        className={`h-14 w-14 rounded-full bg-black/60 border border-white/20 flex items-center justify-center transition-opacity ${
                          playing ? "opacity-0 group-hover:opacity-100" : "opacity-100"
                        }`}
                      >
                        {playing ? (
                          <Pause className="h-6 w-6 text-white" />
                        ) : (
                          <Play className="h-6 w-6 text-white ml-0.5" />
                        )}
                      </span>
                    </button>
                  </div>
                  <p className="text-center text-[11px] text-zinc-500 mt-2">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </p>
                </div>

                <div className="w-full max-w-2xl flex flex-col gap-3">
                  <EditorTimeline
                    duration={duration}
                    start={start}
                    end={end}
                    currentTime={currentTime}
                    onRangeChange={handleRangeChange}
                    onSeek={handleSeek}
                  />
                  <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400">
                    <label className="flex items-center gap-1.5">
                      Başlangıç
                      <input
                        type="number"
                        step="0.1"
                        value={Number(start.toFixed(1))}
                        onChange={(e) => {
                          const v = Math.max(0, Math.min(Number(e.target.value) || 0, end - 1));
                          handleRangeChange(v, end, "start");
                        }}
                        className="w-20 bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-white focus:outline-none focus:border-red-500/60"
                      />
                      sn
                    </label>
                    <label className="flex items-center gap-1.5">
                      Bitiş
                      <input
                        type="number"
                        step="0.1"
                        value={Number(end.toFixed(1))}
                        onChange={(e) => {
                          const v = Math.min(
                            duration || Infinity,
                            Math.max(Number(e.target.value) || 0, start + 1)
                          );
                          handleRangeChange(start, v, "end");
                        }}
                        className="w-20 bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-white focus:outline-none focus:border-red-500/60"
                      />
                      sn
                    </label>
                    <span className="ml-auto text-zinc-300 font-medium">
                      {(end - start).toFixed(1)} sn klip
                    </span>
                  </div>
                  {end - start < 3 && (
                    <p className="text-[11px] text-red-400">Klip en az 3 saniye olmalı.</p>
                  )}
                </div>
              </>
            ) : null}
          </section>

          <aside className="w-full lg:w-80 shrink-0 border-t lg:border-t-0 lg:border-l border-white/10 bg-white/[0.02] p-4 flex flex-col gap-6">
            <div>
              <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
                <Palette className="h-3.5 w-3.5" />
                Altyazı Rengi
              </h3>
              <div className="flex flex-wrap items-center gap-2.5">
                {renderOptions.colors.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setClipColor(c.hex)}
                    title={c.label}
                    aria-label={c.label}
                    style={{ backgroundColor: c.hex }}
                    className={`h-8 w-8 rounded-full border transition ${
                      clipColor.toLowerCase() === c.hex.toLowerCase()
                        ? "ring-2 ring-offset-2 ring-offset-black ring-red-500 border-transparent"
                        : "border-white/20"
                    }`}
                  />
                ))}
              </div>
            </div>

            {(clipAnimation === "karaoke" || clipAnimation === "pop") && (
              <div>
                <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
                  <Palette className="h-3.5 w-3.5" />
                  Vurgu Rengi
                </h3>
                <div className="flex flex-wrap items-center gap-2.5">
                  {renderOptions.colors.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setClipHighlightColor(c.hex)}
                      title={c.label}
                      aria-label={c.label}
                      style={{ backgroundColor: c.hex }}
                      className={`h-8 w-8 rounded-full border transition ${
                        clipHighlightColor.toLowerCase() === c.hex.toLowerCase()
                          ? "ring-2 ring-offset-2 ring-offset-black ring-red-500 border-transparent"
                          : "border-white/20"
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
                <Monitor className="h-3.5 w-3.5" />
                Format
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {renderOptions.aspects.map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => setClipAspect(a.id)}
                    className={`rounded-lg border px-2 py-2 text-[11px] font-semibold transition-colors ${
                      clipAspect === a.id
                        ? "border-red-500 bg-red-500/10 text-red-300"
                        : "border-white/10 bg-black/30 text-zinc-400 hover:border-white/25"
                    }`}
                  >
                    {a.id}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-zinc-500 mt-1.5">
                {renderOptions.aspects.find((a) => a.id === clipAspect)?.label}
              </p>
            </div>

            <div>
              <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
                <AlignCenter className="h-3.5 w-3.5" />
                Altyazı Konumu
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {renderOptions.positions.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setClipPosition(p.id)}
                    className={`rounded-lg border px-2 py-2 text-[11px] font-semibold transition-colors ${
                      clipPosition === p.id
                        ? "border-red-500 bg-red-500/10 text-red-300"
                        : "border-white/10 bg-black/30 text-zinc-400 hover:border-white/25"
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
                <Wand2 className="h-3.5 w-3.5" />
                Altyazı Animasyonu
              </h3>
              <div className="flex flex-col gap-2">
                {renderOptions.animations.map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => setClipAnimation(a.id)}
                    className={`flex items-center justify-between rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                      clipAnimation === a.id
                        ? "border-red-500 bg-red-500/10 text-red-300"
                        : "border-white/10 bg-black/30 text-zinc-400 hover:border-white/25"
                    }`}
                  >
                    {a.label}
                    {clipAnimation === a.id && <Check className="h-3.5 w-3.5 shrink-0" />}
                  </button>
                ))}
              </div>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}
