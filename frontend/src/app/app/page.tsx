"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Pencil, Download, X, Lock, LogOut, UploadCloud, Trash2, Plus, Scissors, Copy, Sparkles, Monitor, CircleStop, Link2, Wand2 } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

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
  social_caption?: string;
  social_hashtags?: string[];
  translations?: { language: string; label: string; url: string }[];
};
type JobStatus =
  | "idle"
  | "queued"
  | "transcribing"
  | "finding_highlights"
  | "rendering"
  | "done"
  | "error";
type JobSummary = {
  job_id: string;
  filename: string;
  status: string;
  created_at: string;
  clips: Clip[];
  aspect?: string;
  credit_cost?: number;
  uploaded_by?: string | null;
};
type RenderOptions = {
  aspects: { id: string; label: string }[];
  positions: { id: string; label: string }[];
  colors: { id: string; label: string; hex: string }[];
  animations: { id: string; label: string }[];
  credits: { base: number; per_clip: number };
};
type Me = {
  user: { id: number; email: string; plan: string; email_verified?: boolean };
  usage: { used: number; limit: number | null; unit?: string };
  effective_plan?: string;
  org?: { id: string; name: string; role: string } | null;
};

const STATUS_LABELS: Record<string, string> = {
  queued: "Sırada bekliyor...",
  transcribing: "Video metne dönüştürülüyor...",
  finding_highlights: "En ilgi çekici anlar bulunuyor...",
  rendering: "Dolgu kelimeler temizleniyor, dikey klipler ve altyazılar oluşturuluyor...",
  done: "Tamamlandı!",
  error: "Bir hata oluştu",
};

const FALLBACK_STYLES: Record<string, string> = {
  klasik: "Klasik",
  vurgu: "Vurgulu (enerjik)",
  minimal: "Minimal",
  kalin: "Kalın (TikTok tarzı)",
  editorial: "Editöryel (dergi tarzı)",
  vintage: "Vintage (retro)",
};

const DURATION_PRESETS: Record<string, { label: string; min: number; max: number }> = {
  kisa: { label: "Kısa (15-30 sn)", min: 15, max: 30 },
  orta: { label: "Orta (20-75 sn)", min: 20, max: 75 },
  uzun: { label: "Uzun (45-90 sn)", min: 45, max: 90 },
};

const CUSTOMIZABLE_PLANS = ["yaratici", "ajans"];

const FALLBACK_RENDER_OPTIONS: RenderOptions = {
  aspects: [
    { id: "9:16", label: "Dikey (9:16) — TikTok / Reels / Shorts" },
    { id: "4:5", label: "Dikey (4:5) — Instagram gönderisi" },
    { id: "1:1", label: "Kare (1:1) — Instagram akışı" },
  ],
  positions: [
    { id: "alt", label: "Alt (varsayılan)" },
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

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

function formatTime(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
}

function scoreColor(score: number): string {
  if (score >= 75) return "text-red-400 bg-red-500/10 border-red-500/20";
  if (score >= 50) return "text-amber-400 bg-amber-500/10 border-amber-500/20";
  return "text-zinc-400 bg-white/5 border-white/10";
}

function RenderOptionsFields({
  styles,
  renderOptions,
  style,
  onStyleChange,
  color,
  onColorChange,
  position,
  onPositionChange,
  aspect,
  onAspectChange,
  animation,
  onAnimationChange,
  highlightColor,
  onHighlightColorChange,
}: {
  styles: Record<string, string>;
  renderOptions: RenderOptions;
  style: string;
  onStyleChange: (v: string) => void;
  color: string;
  onColorChange: (v: string) => void;
  position: string;
  onPositionChange: (v: string) => void;
  aspect: string;
  onAspectChange: (v: string) => void;
  animation: string;
  onAnimationChange: (v: string) => void;
  highlightColor: string;
  onHighlightColorChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <label className="flex-1 text-[11px] font-medium text-zinc-500">
          Altyazı stili
          <select
            value={style}
            onChange={(e) => onStyleChange(e.target.value)}
            className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-red-500/60 transition-colors"
          >
            {Object.entries(styles).map(([key, label]) => (
              <option key={key} value={key} className="bg-black">
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex-1 text-[11px] font-medium text-zinc-500">
          Format
          <select
            value={aspect}
            onChange={(e) => onAspectChange(e.target.value)}
            className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-red-500/60 transition-colors"
          >
            {renderOptions.aspects.map((a) => (
              <option key={a.id} value={a.id} className="bg-black">
                {a.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="text-[11px] font-medium text-zinc-500">
        Altyazı konumu
        <select
          value={position}
          onChange={(e) => onPositionChange(e.target.value)}
          className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-red-500/60 transition-colors"
        >
          {renderOptions.positions.map((pos) => (
            <option key={pos.id} value={pos.id} className="bg-black">
              {pos.label}
            </option>
          ))}
        </select>
      </label>
      <label className="text-[11px] font-medium text-zinc-500">
        Altyazı animasyonu
        <select
          value={animation}
          onChange={(e) => onAnimationChange(e.target.value)}
          className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-red-500/60 transition-colors"
        >
          {renderOptions.animations.map((a) => (
            <option key={a.id} value={a.id} className="bg-black">
              {a.label}
            </option>
          ))}
        </select>
      </label>
      <div>
        <span className="block text-[11px] font-medium text-zinc-500 mb-1.5">Altyazı rengi</span>
        <div className="flex items-center gap-2">
          {renderOptions.colors.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => onColorChange(c.hex)}
              title={c.label}
              aria-label={c.label}
              style={{ backgroundColor: c.hex }}
              className={`h-5 w-5 rounded-full border transition ${
                color.toLowerCase() === c.hex.toLowerCase()
                  ? "ring-2 ring-offset-1 ring-offset-black ring-red-500 border-transparent"
                  : "border-white/20"
              }`}
            />
          ))}
        </div>
      </div>
      {(animation === "karaoke" || animation === "pop") && (
        <div>
          <span className="block text-[11px] font-medium text-zinc-500 mb-1.5">Vurgu rengi</span>
          <div className="flex items-center gap-2">
            {renderOptions.colors.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => onHighlightColorChange(c.hex)}
                title={c.label}
                aria-label={c.label}
                style={{ backgroundColor: c.hex }}
                className={`h-5 w-5 rounded-full border transition ${
                  highlightColor.toLowerCase() === c.hex.toLowerCase()
                    ? "ring-2 ring-offset-1 ring-offset-black ring-red-500 border-transparent"
                    : "border-white/20"
                }`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TrimScrubber({
  jobId,
  token,
  start,
  end,
  onChange,
  onDurationLoaded,
}: {
  jobId: string;
  token: string;
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
  onDurationLoaded?: (duration: number) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [duration, setDuration] = useState(0);
  const [dragging, setDragging] = useState<"start" | "end" | null>(null);
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
        const next = Math.max(0, Math.min(t, curEnd - 1));
        onChange(next, curEnd);
        if (videoRef.current) videoRef.current.currentTime = next;
      } else {
        const next = Math.min(duration || Infinity, Math.max(t, curStart + 1));
        onChange(curStart, next);
        if (videoRef.current) videoRef.current.currentTime = next;
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
  }, [dragging, duration, onChange, timeFromClientX]);

  const startPct = duration ? (start / duration) * 100 : 0;
  const endPct = duration ? (end / duration) * 100 : 100;

  return (
    <div className="flex flex-col gap-2.5">
      <video
        ref={videoRef}
        src={`${API_URL}/api/jobs/${jobId}/source?token=${encodeURIComponent(token)}`}
        onLoadedMetadata={(e) => {
          const d = e.currentTarget.duration;
          setDuration(d);
          onDurationLoaded?.(d);
          e.currentTarget.currentTime = start;
        }}
        muted
        playsInline
        controls
        className="w-full rounded-lg bg-black aspect-video"
      />
      <div
        ref={trackRef}
        className="relative h-9 rounded-lg bg-white/10 select-none touch-none"
      >
        <div
          className="absolute inset-y-0 bg-red-500/25 border-y-2 border-red-500/70"
          style={{ left: `${startPct}%`, right: `${100 - endPct}%` }}
        />
        <div
          onPointerDown={(e) => {
            e.preventDefault();
            setDragging("start");
          }}
          className="absolute inset-y-0 -ml-2 w-4 rounded-md bg-red-500 cursor-ew-resize touch-none shadow-lg"
          style={{ left: `${startPct}%` }}
        />
        <div
          onPointerDown={(e) => {
            e.preventDefault();
            setDragging("end");
          }}
          className="absolute inset-y-0 -ml-2 w-4 rounded-md bg-red-500 cursor-ew-resize touch-none shadow-lg"
          style={{ left: `${endPct}%` }}
        />
      </div>
      <div className="flex justify-between text-[11px] text-zinc-500">
        <span>{formatTime(start)}</span>
        <span className="text-zinc-400 font-medium">{formatTime(end - start)} seçili</span>
        <span>{formatTime(end)}</span>
      </div>
    </div>
  );
}

function ClipCard({
  clip,
  index,
  jobId,
  token,
  onUpdated,
  onDeleted,
  aspectClass,
  styles,
  renderOptions,
  defaultStyle,
  defaultColor,
  defaultPosition,
  defaultAspect,
  defaultAnimation,
  defaultHighlightColor,
  subtitleLanguages,
}: {
  clip: Clip;
  index: number;
  jobId: string | null;
  token: string;
  onUpdated: (index: number, updated: Clip) => void;
  onDeleted: (clips: Clip[]) => void;
  aspectClass: string;
  styles: Record<string, string>;
  renderOptions: RenderOptions;
  defaultStyle: string;
  defaultColor: string;
  defaultPosition: string;
  defaultAspect: string;
  defaultAnimation: string;
  defaultHighlightColor: string;
  subtitleLanguages: { id: string; label: string }[];
}) {
  const [editing, setEditing] = useState(false);
  const [start, setStart] = useState(clip.start ?? 0);
  const [end, setEnd] = useState(clip.end ?? 0);
  const [clipStyle, setClipStyle] = useState(clip.style ?? defaultStyle);
  const [clipColor, setClipColor] = useState(clip.subtitle_color ?? defaultColor);
  const [clipPosition, setClipPosition] = useState(clip.subtitle_position ?? defaultPosition);
  const [clipAspect, setClipAspect] = useState(clip.aspect ?? defaultAspect);
  const [clipAnimation, setClipAnimation] = useState(clip.subtitle_animation ?? defaultAnimation);
  const [clipHighlightColor, setClipHighlightColor] = useState(clip.highlight_color ?? defaultHighlightColor);
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [captionLoading, setCaptionLoading] = useState(false);
  const [captionError, setCaptionError] = useState<string | null>(null);
  const [captionCopied, setCaptionCopied] = useState(false);
  const [translateLoading, setTranslateLoading] = useState(false);
  const [translateError, setTranslateError] = useState<string | null>(null);
  const [translateLang, setTranslateLang] = useState(subtitleLanguages[0]?.id ?? "en");

  async function handleRetrim() {
    if (!jobId) return;
    setSaving(true);
    setEditError(null);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/${index}/retrim`, {
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
        setEditError(data.detail || "Yeniden oluşturulamadı");
        return;
      }
      onUpdated(index, data);
      setEditing(false);
    } catch {
      setEditError("Sunucuya ulaşılamadı");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!jobId) return;
    if (!window.confirm("Bu klibi silmek istediğine emin misin?")) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/${index}`, {
        method: "DELETE",
        headers: authHeaders(token),
      });
      const data = await res.json();
      if (!res.ok) {
        setEditError(data.detail || "Silinemedi");
        return;
      }
      onDeleted(data.clips);
    } catch {
      setEditError("Sunucuya ulaşılamadı");
    } finally {
      setDeleting(false);
    }
  }

  async function handleGenerateCaption() {
    if (!jobId) return;
    setCaptionLoading(true);
    setCaptionError(null);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/${index}/caption`, {
        method: "POST",
        headers: authHeaders(token),
      });
      const data = await res.json();
      if (!res.ok) {
        setCaptionError(data.detail || "Oluşturulamadı");
        return;
      }
      onUpdated(index, data);
    } catch {
      setCaptionError("Sunucuya ulaşılamadı");
    } finally {
      setCaptionLoading(false);
    }
  }

  function handleCopyCaption() {
    const text = `${clip.social_caption ?? ""}\n\n${(clip.social_hashtags ?? []).map((h) => `#${h}`).join(" ")}`;
    navigator.clipboard?.writeText(text).catch(() => {});
    setCaptionCopied(true);
    setTimeout(() => setCaptionCopied(false), 2000);
  }

  async function handleTranslate() {
    if (!jobId) return;
    setTranslateLoading(true);
    setTranslateError(null);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/${index}/translate`, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({ language: translateLang }),
      });
      const data = await res.json();
      if (!res.ok) {
        setTranslateError(data.detail || "Çevrilemedi");
        return;
      }
      onUpdated(index, data);
    } catch {
      setTranslateError("Sunucuya ulaşılamadı");
    } finally {
      setTranslateLoading(false);
    }
  }

  const canEdit = jobId && clip.start !== undefined && clip.end !== undefined;

  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden text-left backdrop-blur-sm hover:border-white/20 transition-colors">
      <video
        key={clip.url}
        src={`${API_URL}${clip.url}`}
        poster={clip.cover_url ? `${API_URL}${clip.cover_url}` : undefined}
        controls
        className={`w-full ${aspectClass} object-cover bg-black`}
      />
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <p className="font-medium text-sm text-white">{clip.title}</p>
          {typeof clip.score === "number" ? (
            <span className={`shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${scoreColor(clip.score)}`}>
              {clip.score}/100
            </span>
          ) : clip.manual ? (
            <span className="shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full border text-zinc-400 bg-white/5 border-white/10">
              Elle eklendi
            </span>
          ) : null}
        </div>
        <p className="text-xs text-zinc-500 mt-1">{clip.reason}</p>

        <div className="mt-3 flex items-center gap-3 text-xs">
          {canEdit && jobId && (
            <Link
              href={`/app/edit/${jobId}/${index}`}
              className="flex items-center gap-1 text-red-400 hover:text-red-300 font-semibold transition-colors"
            >
              <Wand2 className="h-3.5 w-3.5" />
              Profesyonel Düzenle
            </Link>
          )}
          {canEdit && (
            <button
              onClick={() => setEditing((v) => !v)}
              className="flex items-center gap-1 text-zinc-400 hover:text-white font-medium transition-colors"
            >
              {editing ? <X className="h-3.5 w-3.5" /> : <Pencil className="h-3.5 w-3.5" />}
              {editing ? "Vazgeç" : "Hızlı düzenle"}
            </button>
          )}
          {clip.manual && jobId && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex items-center gap-1 text-zinc-500 hover:text-red-400 font-medium transition-colors disabled:opacity-40"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {deleting ? "Siliniyor..." : "Sil"}
            </button>
          )}
          {clip.subtitles_en_url && (
            <a
              href={`${API_URL}${clip.subtitles_en_url}`}
              download
              className="flex items-center gap-1 text-zinc-400 hover:text-white font-medium transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              İngilizce altyazı (.srt)
            </a>
          )}
        </div>

        {canEdit && jobId && (
          <div className="mt-3 pt-3 border-t border-white/10 flex flex-col gap-2.5">
            {clip.social_caption ? (
              <div className="rounded-lg bg-black/30 border border-white/10 px-3 py-2.5">
                <p className="text-xs text-zinc-300 leading-relaxed">{clip.social_caption}</p>
                {clip.social_hashtags && clip.social_hashtags.length > 0 && (
                  <p className="mt-1.5 text-[11px] text-red-400">
                    {clip.social_hashtags.map((h) => `#${h}`).join(" ")}
                  </p>
                )}
                <button
                  onClick={handleCopyCaption}
                  className="mt-2 flex items-center gap-1 text-[11px] text-zinc-400 hover:text-white font-medium transition-colors"
                >
                  <Copy className="h-3 w-3" />
                  {captionCopied ? "Kopyalandı ✓" : "Metni kopyala"}
                </button>
              </div>
            ) : (
              <button
                onClick={handleGenerateCaption}
                disabled={captionLoading}
                className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-white font-medium transition-colors disabled:opacity-40 w-fit"
              >
                <Sparkles className="h-3 w-3" />
                {captionLoading ? "Oluşturuluyor..." : "Paylaşım metni ve hashtag oluştur"}
              </button>
            )}
            {captionError && (
              <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-2 py-1.5">
                {captionError}
              </p>
            )}

            <div className="flex flex-wrap items-center gap-2.5">
              {(clip.translations ?? []).map((t) => (
                <a
                  key={t.language}
                  href={`${API_URL}${t.url}`}
                  download
                  className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-white font-medium transition-colors"
                >
                  <Download className="h-3 w-3" />
                  {t.label} (.srt)
                </a>
              ))}
              <select
                value={translateLang}
                onChange={(e) => setTranslateLang(e.target.value)}
                className="bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-red-500/60 transition-colors"
              >
                {subtitleLanguages.map((l) => (
                  <option key={l.id} value={l.id} className="bg-black">
                    {l.label}
                  </option>
                ))}
              </select>
              <button
                onClick={handleTranslate}
                disabled={translateLoading}
                className="text-[11px] text-red-400 hover:text-red-300 font-medium transition-colors disabled:opacity-40"
              >
                {translateLoading ? "Çevriliyor..." : "+ Altyazı ekle"}
              </button>
            </div>
            {translateError && (
              <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-2 py-1.5">
                {translateError}
              </p>
            )}
          </div>
        )}

        {editing && canEdit && jobId && (
          <div className="mt-3 pt-3 border-t border-white/10 flex flex-col gap-2">
            <p className="text-[11px] text-zinc-500">
              Tutamaçları sürükleyerek klibin nereden başlayıp nerede biteceğini seç
            </p>
            <TrimScrubber
              jobId={jobId}
              token={token}
              start={start}
              end={end}
              onChange={(s, e) => {
                setStart(s);
                setEnd(e);
              }}
            />
            <div className="pt-1 border-t border-white/5">
              <p className="text-[11px] text-zinc-500 mt-2 mb-1.5">
                Bu klip için altyazı stilini ve formatını ayrıca değiştirebilirsin
              </p>
              <RenderOptionsFields
                styles={styles}
                renderOptions={renderOptions}
                style={clipStyle}
                onStyleChange={setClipStyle}
                color={clipColor}
                onColorChange={setClipColor}
                position={clipPosition}
                onPositionChange={setClipPosition}
                aspect={clipAspect}
                onAspectChange={setClipAspect}
                animation={clipAnimation}
                onAnimationChange={setClipAnimation}
                highlightColor={clipHighlightColor}
                onHighlightColorChange={setClipHighlightColor}
              />
            </div>
            {editError && (
              <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-2 py-1.5">
                {editError}
              </p>
            )}
            <button
              onClick={handleRetrim}
              disabled={saving || end - start < 3}
              className="mt-1 bg-red-500 text-black px-4 py-2 rounded-lg text-xs font-semibold hover:bg-red-600 transition disabled:opacity-40"
            >
              {saving ? "Yeniden oluşturuluyor..." : "Yeniden oluştur"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function AddClipCard({
  jobId,
  token,
  aspectClass,
  onAdded,
  styles,
  renderOptions,
  defaultStyle,
  defaultColor,
  defaultPosition,
  defaultAspect,
  defaultAnimation,
  defaultHighlightColor,
}: {
  jobId: string;
  token: string;
  aspectClass: string;
  onAdded: (clips: Clip[]) => void;
  styles: Record<string, string>;
  renderOptions: RenderOptions;
  defaultStyle: string;
  defaultColor: string;
  defaultPosition: string;
  defaultAspect: string;
  defaultAnimation: string;
  defaultHighlightColor: string;
}) {
  const [open, setOpen] = useState(false);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(30);
  const [durationKnown, setDurationKnown] = useState(false);
  const [title, setTitle] = useState("");
  const [clipStyle, setClipStyle] = useState(defaultStyle);
  const [clipColor, setClipColor] = useState(defaultColor);
  const [clipPosition, setClipPosition] = useState(defaultPosition);
  const [clipAspect, setClipAspect] = useState(defaultAspect);
  const [clipAnimation, setClipAnimation] = useState(defaultAnimation);
  const [clipHighlightColor, setClipHighlightColor] = useState(defaultHighlightColor);
  const [saving, setSaving] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  async function handleAdd() {
    setSaving(true);
    setAddError(null);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/add`, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({
          start,
          end,
          title: title.trim() || undefined,
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
        setAddError(data.detail || "Klip oluşturulamadı");
        return;
      }
      onAdded(data.clips);
      setOpen(false);
      setTitle("");
    } catch {
      setAddError("Sunucuya ulaşılamadı");
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className={`flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-white/[0.02] hover:border-red-500/40 hover:bg-white/[0.04] transition-colors text-zinc-400 hover:text-white ${aspectClass}`}
      >
        <Plus className="h-5 w-5" />
        <span className="text-sm font-medium">Yeni klip ekle</span>
        <span className="text-[11px] text-zinc-500 px-4 text-center">
          Videonun istediğin herhangi bir anından elle klip oluştur
        </span>
      </button>
    );
  }

  return (
    <div className="bg-white/[0.03] border border-red-500/30 rounded-xl overflow-hidden text-left backdrop-blur-sm p-3 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-white flex items-center gap-1.5">
          <Scissors className="h-3.5 w-3.5 text-red-400" />
          Yeni klip
        </p>
        <button onClick={() => setOpen(false)} className="text-zinc-500 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="text-[11px] text-zinc-500">
        Tutamaçları sürükleyerek videonun hangi aralığının klip olacağını seç
      </p>
      <TrimScrubber
        jobId={jobId}
        token={token}
        start={start}
        end={end}
        onChange={(s, e) => {
          setStart(s);
          setEnd(e);
        }}
        onDurationLoaded={(d) => {
          if (!durationKnown) {
            setEnd(Math.min(30, d));
            setDurationKnown(true);
          }
        }}
      />
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Klip başlığı (opsiyonel)"
        className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
      />
      <RenderOptionsFields
        styles={styles}
        renderOptions={renderOptions}
        style={clipStyle}
        onStyleChange={setClipStyle}
        color={clipColor}
        onColorChange={setClipColor}
        position={clipPosition}
        onPositionChange={setClipPosition}
        aspect={clipAspect}
        onAspectChange={setClipAspect}
        animation={clipAnimation}
        onAnimationChange={setClipAnimation}
        highlightColor={clipHighlightColor}
        onHighlightColorChange={setClipHighlightColor}
      />
      {addError && (
        <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-2 py-1.5">
          {addError}
        </p>
      )}
      <button
        onClick={handleAdd}
        disabled={saving || end - start < 3}
        className="bg-red-500 text-black px-4 py-2 rounded-lg text-xs font-semibold hover:bg-red-600 transition disabled:opacity-40"
      >
        {saving ? "Oluşturuluyor..." : "Klip oluştur"}
      </button>
    </div>
  );
}

export default function AppPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [history, setHistory] = useState<JobSummary[]>([]);

  const [file, setFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<"dosya" | "link">("dosya");
  const [videoUrl, setVideoUrl] = useState("");
  const [status, setStatus] = useState<JobStatus>("idle");
  const [clips, setClips] = useState<Clip[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [styles, setStyles] = useState<Record<string, string>>(FALLBACK_STYLES);
  const [style, setStyle] = useState("klasik");
  const [removeFillers, setRemoveFillers] = useState(true);
  const [clipCount, setClipCount] = useState(5);
  const [durationPreset, setDurationPreset] = useState("orta");
  const [renderOptions, setRenderOptions] = useState<RenderOptions>(FALLBACK_RENDER_OPTIONS);
  const [subtitleColor, setSubtitleColor] = useState("#FFFFFF");
  const [subtitlePosition, setSubtitlePosition] = useState("alt");
  const [aspect, setAspect] = useState("9:16");
  const [subtitleAnimation, setSubtitleAnimation] = useState("statik");
  const [subtitleHighlightColor, setSubtitleHighlightColor] = useState("#FFEB3B");
  const [currentAspect, setCurrentAspect] = useState("9:16");
  const [currentStyle, setCurrentStyle] = useState("klasik");
  const [currentSubtitleColor, setCurrentSubtitleColor] = useState("#FFFFFF");
  const [currentSubtitlePosition, setCurrentSubtitlePosition] = useState("alt");
  const [currentSubtitleAnimation, setCurrentSubtitleAnimation] = useState("statik");
  const [currentSubtitleHighlightColor, setCurrentSubtitleHighlightColor] = useState("#FFEB3B");
  const [subtitleLanguages, setSubtitleLanguages] = useState<{ id: string; label: string }[]>([
    { id: "en", label: "İngilizce" },
  ]);
  const [resendingVerification, setResendingVerification] = useState(false);
  const [verificationResent, setVerificationResent] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [recordError, setRecordError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordChunksRef = useRef<Blob[]>([]);
  const recordTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recordStreamRef = useRef<MediaStream | null>(null);

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
    fetch(`${API_URL}/api/auth/me`, { headers: authHeaders(token) })
      .then(async (r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(setMe)
      .catch(() => {
        localStorage.removeItem("klipster_token");
        router.push("/giris");
      });

    fetch(`${API_URL}/api/jobs`, { headers: authHeaders(token) })
      .then((r) => r.json())
      .then(setHistory)
      .catch(() => {});

    fetch(`${API_URL}/api/caption-styles`)
      .then((r) => r.json())
      .then((data) => {
        if (data && Object.keys(data).length > 0) setStyles(data);
      })
      .catch(() => {});

    fetch(`${API_URL}/api/render-options`)
      .then((r) => r.json())
      .then((data) => {
        if (
          data &&
          data.aspects?.length &&
          data.positions?.length &&
          data.colors?.length &&
          data.animations?.length &&
          data.credits
        ) {
          setRenderOptions(data);
        }
      })
      .catch(() => {});

    fetch(`${API_URL}/api/subtitle-languages`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) setSubtitleLanguages(data);
      })
      .catch(() => {});
  }, [token, router]);

  // Profesyonel düzenleyiciden "Kaydet" sonrası geri dönüldüğünde
  // (/app?job=<id>), o işi otomatik olarak açıp güncel klipleri gösterir -
  // aksi halde sayfa yeniden mount olduğu için düzenlenen klip görünmez kalırdı.
  useEffect(() => {
    if (!token) return;
    const jobParam = new URLSearchParams(window.location.search).get("job");
    if (jobParam) {
      handleOpenHistoryJob(jobParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    return () => {
      if (recordTimerRef.current) clearInterval(recordTimerRef.current);
      recordStreamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function handleStartRecording() {
    setRecordError(null);
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      recordStreamRef.current = stream;
      recordChunksRef.current = [];
      const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
        ? "video/webm;codecs=vp9,opus"
        : "video/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordChunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(recordChunksRef.current, { type: mimeType });
        const recordedFile = new File([blob], `ekran-kaydi-${Date.now()}.webm`, { type: mimeType });
        setFile(recordedFile);
        stream.getTracks().forEach((t) => t.stop());
        recordStreamRef.current = null;
        setRecording(false);
        if (recordTimerRef.current) {
          clearInterval(recordTimerRef.current);
          recordTimerRef.current = null;
        }
      };
      // kullanici tarayicinin kendi "Paylaşımı durdur" dugmesine basarsa
      // (bizim durdur butonumuzu kullanmadan) kaydi da otomatik sonlandir
      stream.getVideoTracks()[0]?.addEventListener("ended", () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
          mediaRecorderRef.current.stop();
        }
      });
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setRecordSeconds(0);
      recordTimerRef.current = setInterval(() => setRecordSeconds((s) => s + 1), 1000);
    } catch {
      setRecordError("Ekran kaydı başlatılamadı - izin vermen gerekiyor");
    }
  }

  function handleStopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  }

  function handleLogout() {
    localStorage.removeItem("klipster_token");
    router.push("/giris");
  }

  function handleClipUpdated(index: number, updated: Clip) {
    setClips((prev) => prev.map((c, i) => (i === index ? updated : c)));
  }

  function handleClipsReplaced(updatedClips: Clip[]) {
    setClips(updatedClips);
    if (token) {
      fetch(`${API_URL}/api/auth/me`, { headers: authHeaders(token) })
        .then((r) => r.json())
        .then(setMe)
        .catch(() => {});
    }
  }

  async function handleOpenHistoryJob(jobId: string) {
    if (!token) return;
    setError(null);
    const res = await fetch(`${API_URL}/api/jobs/${jobId}`, { headers: authHeaders(token) });
    if (!res.ok) return;
    const jobData = await res.json();
    setCurrentJobId(jobId);
    setClips(jobData.clips || []);
    setCurrentAspect(jobData.aspect || "9:16");
    setCurrentStyle(jobData.style || "klasik");
    setCurrentSubtitleColor(jobData.subtitle_color || "#FFFFFF");
    setCurrentSubtitlePosition(jobData.subtitle_position || "alt");
    setCurrentSubtitleAnimation(jobData.subtitle_animation || "statik");
    setCurrentSubtitleHighlightColor(jobData.highlight_color || "#FFEB3B");
    setStatus("done");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const canCustomize = !!me && CUSTOMIZABLE_PLANS.includes(me.effective_plan ?? me.user.plan);

  function trackJob(jobId: string) {
    setCurrentJobId(jobId);
    const poll = setInterval(async () => {
      if (!token) return;
      const r = await fetch(`${API_URL}/api/jobs/${jobId}`, { headers: authHeaders(token) });
      const jobData = await r.json();
      setStatus(jobData.status);
      if (jobData.status === "done") {
        setClips(jobData.clips);
        setCurrentAspect(jobData.aspect || "9:16");
        setCurrentStyle(jobData.style || "klasik");
        setCurrentSubtitleColor(jobData.subtitle_color || "#FFFFFF");
        setCurrentSubtitlePosition(jobData.subtitle_position || "alt");
        setCurrentSubtitleAnimation(jobData.subtitle_animation || "statik");
    setCurrentSubtitleHighlightColor(jobData.highlight_color || "#FFEB3B");
        clearInterval(poll);
        fetch(`${API_URL}/api/auth/me`, { headers: authHeaders(token) }).then((r) => r.json()).then(setMe);
        fetch(`${API_URL}/api/jobs`, { headers: authHeaders(token) }).then((r) => r.json()).then(setHistory);
      }
      if (jobData.status === "error") {
        setError(jobData.error);
        clearInterval(poll);
      }
    }, 3000);
  }

  async function handleUpload() {
    if (!token) return;
    if (uploadMode === "dosya" && !file) return;
    if (uploadMode === "link" && !videoUrl.trim()) return;
    setStatus("queued");
    setClips([]);
    setCurrentJobId(null);
    setError(null);

    const preset = DURATION_PRESETS[durationPreset] ?? DURATION_PRESETS.orta;

    let res: Response;
    if (uploadMode === "link") {
      // YouTube (veya yt-dlp'nin destekledigi baska bir site) linkinden
      // yukleme - sunucu videoyu indirip sanki bilgisayardan yuklenmis
      // gibi AYNI klip uretim hattina sokuyor (bkz. backend _start_processing_job).
      const body: Record<string, unknown> = {
        url: videoUrl.trim(),
        style,
        remove_fillers: removeFillers,
        subtitle_color: subtitleColor,
        subtitle_position: subtitlePosition,
        aspect,
        subtitle_animation: subtitleAnimation,
        highlight_color: subtitleHighlightColor,
      };
      if (canCustomize) {
        body.clip_count = clipCount;
        body.min_duration = preset.min;
        body.max_duration = preset.max;
      }
      res = await fetch(`${API_URL}/api/upload-url`, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } else {
      const formData = new FormData();
      formData.append("file", file as File);
      formData.append("style", style);
      formData.append("remove_fillers", String(removeFillers));
      formData.append("subtitle_color", subtitleColor);
      formData.append("subtitle_position", subtitlePosition);
      formData.append("aspect", aspect);
      formData.append("subtitle_animation", subtitleAnimation);
      formData.append("highlight_color", subtitleHighlightColor);
      if (canCustomize) {
        formData.append("clip_count", String(clipCount));
        formData.append("min_duration", String(preset.min));
        formData.append("max_duration", String(preset.max));
      }
      res = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        headers: authHeaders(token),
        body: formData,
      });
    }

    const data = await res.json();
    if (!res.ok) {
      setStatus("error");
      setError(data.detail || "Yükleme başarısız");
      return;
    }
    trackJob(data.job_id);
  }

  const isBusy = status !== "idle" && status !== "done" && status !== "error";

  if (!token) return null;

  const limitReached = me?.usage.limit !== null && me?.usage.limit !== undefined && me.usage.used >= me.usage.limit;
  const effectiveClipCount = canCustomize ? clipCount : 5;
  const estimatedCost = renderOptions.credits.base + effectiveClipCount * renderOptions.credits.per_clip;

  return (
    <main className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0202] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-red-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <header className="fixed top-0 left-0 w-full z-50 pt-6 px-4">
        <div className="max-w-5xl mx-auto relative">
          <div className="absolute -inset-2 rounded-full bg-red-600/20 blur-xl animate-glow pointer-events-none" />
        <nav className="relative flex items-center justify-between gap-4 bg-black/60 backdrop-blur-xl border border-red-500/25 rounded-full px-6 py-3 shadow-[0_0_25px_rgba(239,68,68,0.15)] transition-all duration-500 hover:border-red-500/45 hover:shadow-[0_0_35px_rgba(239,68,68,0.25)]">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <Logo className="h-14" />
          </Link>
          <div className="flex items-center gap-4 text-sm min-w-0">
            {me && (
              <span className="text-zinc-400 truncate hidden sm:inline">
                {me.user.email} · {me.usage.used}/{me.usage.limit ?? "∞"} kredi (bu ay)
              </span>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-zinc-400 hover:text-white transition-colors shrink-0"
            >
              <LogOut className="h-3.5 w-3.5" />
              Çıkış yap
            </button>
          </div>
        </nav>
        </div>
      </header>

      <div className="relative z-10 max-w-2xl mx-auto px-6 pt-32 pb-20 flex flex-col items-center text-center gap-6">
        {me && !me.user.email_verified && (
          <div className="w-full flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-left">
            <p className="text-sm text-red-200">E-posta adresini henüz doğrulamadın.</p>
            <button
              onClick={async () => {
                if (!token) return;
                setResendingVerification(true);
                try {
                  await fetch(`${API_URL}/api/auth/resend-verification`, {
                    method: "POST",
                    headers: authHeaders(token),
                  });
                  setVerificationResent(true);
                  setTimeout(() => setVerificationResent(false), 4000);
                } finally {
                  setResendingVerification(false);
                }
              }}
              disabled={resendingVerification}
              className="text-xs font-semibold text-red-400 hover:text-red-300 transition-colors disabled:opacity-40"
            >
              {verificationResent
                ? "Gönderildi ✓"
                : resendingVerification
                ? "Gönderiliyor..."
                : "Doğrulama e-postasını tekrar gönder"}
            </button>
          </div>
        )}

        <h1 className="text-3xl sm:text-4xl font-display font-semibold tracking-tight">Video Yükle</h1>
        <p className="text-zinc-400">
          Uzun videonu yükle, yapay zeka en ilgi çekici anları bulup senin
          için altyazılı, dikey kısa klipler oluştursun.
        </p>

        {limitReached && (
          <p className="text-sm bg-red-500/10 border border-red-500/20 text-red-300 rounded-lg px-4 py-3 w-full text-left">
            Bu ayki kredin doldu ({me?.usage.used}/{me?.usage.limit} kredi). Daha fazla video için bir üst plana geçmen gerekiyor.
          </p>
        )}

        <div className="w-full rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 sm:p-10 flex flex-col items-center gap-6 shadow-2xl">
          {!recording && (
            <div className="w-full flex items-center gap-1.5 bg-black/30 border border-white/10 rounded-full p-1">
              <button
                type="button"
                onClick={() => setUploadMode("dosya")}
                className={`flex-1 flex items-center justify-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                  uploadMode === "dosya" ? "bg-red-500 text-black" : "text-zinc-400 hover:text-white"
                }`}
              >
                <UploadCloud className="h-3.5 w-3.5" />
                Dosya yükle
              </button>
              <button
                type="button"
                onClick={() => setUploadMode("link")}
                className={`flex-1 flex items-center justify-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                  uploadMode === "link" ? "bg-red-500 text-black" : "text-zinc-400 hover:text-white"
                }`}
              >
                <Link2 className="h-3.5 w-3.5" />
                Link ile yükle
              </button>
            </div>
          )}

          {recording ? (
            <div className="w-full flex flex-col items-center gap-3 border border-red-500/30 bg-red-500/[0.06] rounded-xl px-6 py-8">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
              </span>
              <span className="text-sm text-red-300 font-medium">
                Ekran kaydediliyor... {formatTime(recordSeconds)}
              </span>
              <button
                onClick={handleStopRecording}
                className="flex items-center gap-1.5 bg-red-500 text-white px-4 py-2 rounded-full text-xs font-semibold hover:bg-red-600 transition"
              >
                <CircleStop className="h-3.5 w-3.5" />
                Kaydı durdur
              </button>
            </div>
          ) : uploadMode === "link" ? (
            <div className="w-full flex flex-col items-center gap-2">
              <label className="w-full flex items-center gap-3 border border-dashed border-white/15 rounded-xl px-4 py-4 focus-within:border-red-500/40 transition-colors">
                <Link2 className="h-5 w-5 text-zinc-500 shrink-0" />
                <input
                  type="url"
                  inputMode="url"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  placeholder="YouTube video linkini yapıştır"
                  className="w-full bg-transparent text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none"
                />
              </label>
              <p className="text-[11px] text-zinc-500 text-center">
                Linki yapıştır, videoyu bilgisayarına indirmene gerek yok - biz indirip
                doğrudan klip oluşturmaya başlarız.
              </p>
            </div>
          ) : (
            <>
              <label className="w-full flex flex-col items-center gap-3 border border-dashed border-white/15 rounded-xl px-6 py-8 cursor-pointer hover:border-red-500/40 hover:bg-white/[0.02] transition-colors">
                <UploadCloud className="h-6 w-6 text-zinc-500" />
                <span className="text-sm text-zinc-300 font-medium">
                  {file ? file.name : "Video seçmek için tıkla"}
                </span>
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="hidden"
                />
              </label>
              <button
                type="button"
                onClick={handleStartRecording}
                className="flex items-center gap-1.5 text-xs font-medium text-zinc-400 hover:text-white transition-colors -mt-2"
              >
                <Monitor className="h-3.5 w-3.5" />
                veya ekranını kaydet
              </button>
            </>
          )}
          {recordError && (
            <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 w-full text-center">
              {recordError}
            </p>
          )}

          <div className="w-full flex flex-col sm:flex-row gap-3 text-left">
            <label className="flex-1 text-xs font-medium text-zinc-400">
              Altyazı stili
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/60 transition-colors"
              >
                {Object.entries(styles).map(([key, label]) => (
                  <option key={key} value={key} className="bg-black">
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex-1 flex items-center gap-2 text-xs font-medium text-zinc-400 sm:pt-5">
              <input
                type="checkbox"
                checked={removeFillers}
                onChange={(e) => setRemoveFillers(e.target.checked)}
                className="h-4 w-4 accent-red-500"
              />
              Konuşma akışını bozan dolgu kelimeleri ve gereksiz
              sessizlikleri otomatik olarak ayıkla
            </label>
          </div>

          <div className="w-full flex flex-col sm:flex-row gap-3 text-left">
            <label className="flex-1 text-xs font-medium text-zinc-400">
              Klip formatı
              <select
                value={aspect}
                onChange={(e) => setAspect(e.target.value)}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/60 transition-colors"
              >
                {renderOptions.aspects.map((a) => (
                  <option key={a.id} value={a.id} className="bg-black">
                    {a.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex-1 text-xs font-medium text-zinc-400">
              Altyazı konumu
              <select
                value={subtitlePosition}
                onChange={(e) => setSubtitlePosition(e.target.value)}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/60 transition-colors"
              >
                {renderOptions.positions.map((p) => (
                  <option key={p.id} value={p.id} className="bg-black">
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="w-full flex flex-col sm:flex-row gap-3 text-left">
            <label className="flex-1 text-xs font-medium text-zinc-400">
              Altyazı animasyonu
              <select
                value={subtitleAnimation}
                onChange={(e) => setSubtitleAnimation(e.target.value)}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/60 transition-colors"
              >
                {renderOptions.animations.map((a) => (
                  <option key={a.id} value={a.id} className="bg-black">
                    {a.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="w-full text-left">
            <span className="block text-xs font-medium text-zinc-400 mb-2">Altyazı rengi</span>
            <div className="flex items-center gap-2.5">
              {renderOptions.colors.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setSubtitleColor(c.hex)}
                  title={c.label}
                  aria-label={c.label}
                  style={{ backgroundColor: c.hex }}
                  className={`h-7 w-7 rounded-full border transition ${
                    subtitleColor.toLowerCase() === c.hex.toLowerCase()
                      ? "ring-2 ring-offset-2 ring-offset-black ring-red-500 border-transparent"
                      : "border-white/20"
                  }`}
                />
              ))}
            </div>
          </div>

          {(subtitleAnimation === "karaoke" || subtitleAnimation === "pop") && (
            <div className="w-full text-left">
              <span className="block text-xs font-medium text-zinc-400 mb-2">Vurgu rengi</span>
              <div className="flex items-center gap-2.5">
                {renderOptions.colors.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setSubtitleHighlightColor(c.hex)}
                    title={c.label}
                    aria-label={c.label}
                    style={{ backgroundColor: c.hex }}
                    className={`h-7 w-7 rounded-full border transition ${
                      subtitleHighlightColor.toLowerCase() === c.hex.toLowerCase()
                        ? "ring-2 ring-offset-2 ring-offset-black ring-red-500 border-transparent"
                        : "border-white/20"
                    }`}
                  />
                ))}
              </div>
            </div>
          )}

          <div className="w-full text-left">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-zinc-400">Klip sayısı ve süresi</span>
              {!canCustomize && (
                <span className="flex items-center gap-1 text-[10px] font-semibold text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full">
                  <Lock className="h-2.5 w-2.5" />
                  Yaratıcı planında
                </span>
              )}
            </div>
            <div className="w-full flex flex-col sm:flex-row gap-3">
              <label className="flex-1 text-xs font-medium text-zinc-400">
                Klip sayısı
                <select
                  value={clipCount}
                  onChange={(e) => setClipCount(Number(e.target.value))}
                  disabled={!canCustomize}
                  className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/60 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {[3, 4, 5, 6, 7, 8].map((n) => (
                    <option key={n} value={n} className="bg-black">
                      {n} klip
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex-1 text-xs font-medium text-zinc-400">
                Klip süresi
                <select
                  value={durationPreset}
                  onChange={(e) => setDurationPreset(e.target.value)}
                  disabled={!canCustomize}
                  className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/60 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {Object.entries(DURATION_PRESETS).map(([key, p]) => (
                    <option key={key} value={key} className="bg-black">
                      {p.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {!canCustomize && (
              <p className="mt-1.5 text-[11px] text-zinc-500">
                Ücretsiz planda otomatik olarak 5 klip, 20-75 sn aralığında üretilir.{" "}
                <Link href="/#fiyatlandirma" className="text-red-400 hover:underline">
                  Yaratıcı planını incele
                </Link>
              </p>
            )}
          </div>

          <p className="text-[11px] text-zinc-500">
            Tahmini maliyet: en az <span className="text-zinc-300 font-medium">{estimatedCost} kredi</span> — video
            uzunluğuna göre artabilir.
          </p>

          <button
            onClick={handleUpload}
            disabled={(uploadMode === "dosya" ? !file : !videoUrl.trim()) || isBusy || limitReached}
            className="bg-red-500 text-black px-8 py-2.5 rounded-full font-semibold text-sm hover:bg-red-600 transition disabled:opacity-30 disabled:hover:bg-red-500"
          >
            Klipleri Oluştur
          </button>
        </div>

        {status !== "idle" && (
          <div className="flex items-center gap-2 text-zinc-400 text-sm">
            {isBusy && (
              <span className="h-3.5 w-3.5 rounded-full border-2 border-white/20 border-t-red-500 animate-spin" />
            )}
            <span>{STATUS_LABELS[status]}</span>
          </div>
        )}
        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 w-full text-left">
            {error}
          </p>
        )}

        {(clips.length > 0 || (currentJobId && status === "done")) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full mt-4">
            {clips.map((clip, i) => (
              <ClipCard
                key={i}
                clip={clip}
                index={i}
                jobId={currentJobId}
                token={token}
                onUpdated={handleClipUpdated}
                onDeleted={handleClipsReplaced}
                aspectClass={ASPECT_CLASS[clip.aspect || currentAspect] || ASPECT_CLASS["9:16"]}
                styles={styles}
                renderOptions={renderOptions}
                defaultStyle={currentStyle}
                defaultColor={currentSubtitleColor}
                defaultPosition={currentSubtitlePosition}
                defaultAspect={currentAspect}
                defaultAnimation={currentSubtitleAnimation}
                defaultHighlightColor={currentSubtitleHighlightColor}
                subtitleLanguages={subtitleLanguages}
              />
            ))}
            {currentJobId && status === "done" && (
              <AddClipCard
                jobId={currentJobId}
                token={token}
                aspectClass={ASPECT_CLASS[currentAspect] || ASPECT_CLASS["9:16"]}
                onAdded={handleClipsReplaced}
                styles={styles}
                renderOptions={renderOptions}
                defaultStyle={currentStyle}
                defaultColor={currentSubtitleColor}
                defaultPosition={currentSubtitlePosition}
                defaultAspect={currentAspect}
                defaultAnimation={currentSubtitleAnimation}
                defaultHighlightColor={currentSubtitleHighlightColor}
              />
            )}
          </div>
        )}

        {history.length > 0 && (
          <div className="w-full mt-14 text-left">
            <h2 className="font-display font-semibold text-lg mb-4">
              {me?.org ? "Ekibin geçmiş videoları" : "Geçmiş videoların"}
            </h2>
            <div className="flex flex-col divide-y divide-white/10 border border-white/10 rounded-xl overflow-hidden bg-white/[0.03] backdrop-blur-sm">
              {history.map((job) => (
                <button
                  key={job.job_id}
                  onClick={() => job.status === "done" && handleOpenHistoryJob(job.job_id)}
                  disabled={job.status !== "done"}
                  className={`flex items-center justify-between px-4 py-3 text-sm text-left w-full transition-colors ${
                    job.status === "done" ? "hover:bg-white/[0.05] cursor-pointer" : "cursor-default"
                  } ${job.job_id === currentJobId ? "bg-red-500/[0.06]" : ""}`}
                >
                  <div className="min-w-0">
                    <p className="font-medium text-zinc-200 truncate max-w-[220px]">{job.filename}</p>
                    <p className="text-xs text-zinc-500">
                      {new Date(job.created_at.replace(" ", "T") + "Z").toLocaleString("tr-TR")}
                      {me?.org && job.uploaded_by ? ` · ${job.uploaded_by}` : ""}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 text-xs font-medium px-2.5 py-1 rounded-full border ${
                      job.status === "done"
                        ? "bg-green-500/10 text-green-400 border-green-500/20"
                        : job.status === "error"
                        ? "bg-red-500/10 text-red-400 border-red-500/20"
                        : "bg-white/5 text-zinc-400 border-white/10"
                    }`}
                  >
                    {job.status === "done"
                      ? `${job.clips?.length ?? 0} klip${job.credit_cost ? ` · ${job.credit_cost} kredi` : ""}`
                      : STATUS_LABELS[job.status] ?? job.status}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
