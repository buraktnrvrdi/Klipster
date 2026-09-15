"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Pencil, Download, X, Lock, LogOut, UploadCloud } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";

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
  if (score >= 75) return "text-orange-400 bg-orange-500/10 border-orange-500/20";
  if (score >= 50) return "text-amber-400 bg-amber-500/10 border-amber-500/20";
  return "text-zinc-400 bg-white/5 border-white/10";
}

function TrimScrubber({
  jobId,
  token,
  start,
  end,
  onChange,
}: {
  jobId: string;
  token: string;
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
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
          className="absolute inset-y-0 bg-orange-500/25 border-y-2 border-orange-500/70"
          style={{ left: `${startPct}%`, right: `${100 - endPct}%` }}
        />
        <div
          onPointerDown={(e) => {
            e.preventDefault();
            setDragging("start");
          }}
          className="absolute inset-y-0 -ml-2 w-4 rounded-md bg-orange-500 cursor-ew-resize touch-none shadow-lg"
          style={{ left: `${startPct}%` }}
        />
        <div
          onPointerDown={(e) => {
            e.preventDefault();
            setDragging("end");
          }}
          className="absolute inset-y-0 -ml-2 w-4 rounded-md bg-orange-500 cursor-ew-resize touch-none shadow-lg"
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
  aspectClass,
}: {
  clip: Clip;
  index: number;
  jobId: string | null;
  token: string;
  onUpdated: (index: number, updated: Clip) => void;
  aspectClass: string;
}) {
  const [editing, setEditing] = useState(false);
  const [start, setStart] = useState(clip.start ?? 0);
  const [end, setEnd] = useState(clip.end ?? 0);
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  async function handleRetrim() {
    if (!jobId) return;
    setSaving(true);
    setEditError(null);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips/${index}/retrim`, {
        method: "POST",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify({ start, end }),
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
          {typeof clip.score === "number" && (
            <span className={`shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${scoreColor(clip.score)}`}>
              {clip.score}/100
            </span>
          )}
        </div>
        <p className="text-xs text-zinc-500 mt-1">{clip.reason}</p>

        <div className="mt-3 flex items-center gap-3 text-xs">
          {canEdit && (
            <button
              onClick={() => setEditing((v) => !v)}
              className="flex items-center gap-1 text-zinc-400 hover:text-white font-medium transition-colors"
            >
              {editing ? <X className="h-3.5 w-3.5" /> : <Pencil className="h-3.5 w-3.5" />}
              {editing ? "Vazgeç" : "Düzenle"}
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
            {editError && (
              <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-2 py-1.5">
                {editError}
              </p>
            )}
            <button
              onClick={handleRetrim}
              disabled={saving || end - start < 3}
              className="mt-1 bg-orange-500 text-black px-4 py-2 rounded-lg text-xs font-semibold hover:bg-orange-600 transition disabled:opacity-40"
            >
              {saving ? "Yeniden oluşturuluyor..." : "Yeniden oluştur"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AppPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [history, setHistory] = useState<JobSummary[]>([]);

  const [file, setFile] = useState<File | null>(null);
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
  const [currentAspect, setCurrentAspect] = useState("9:16");
  const [resendingVerification, setResendingVerification] = useState(false);
  const [verificationResent, setVerificationResent] = useState(false);

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
        if (data && data.aspects?.length && data.positions?.length && data.colors?.length && data.credits) {
          setRenderOptions(data);
        }
      })
      .catch(() => {});
  }, [token, router]);

  function handleLogout() {
    localStorage.removeItem("klipster_token");
    router.push("/giris");
  }

  function handleClipUpdated(index: number, updated: Clip) {
    setClips((prev) => prev.map((c, i) => (i === index ? updated : c)));
  }

  const canCustomize = !!me && CUSTOMIZABLE_PLANS.includes(me.effective_plan ?? me.user.plan);

  async function handleUpload() {
    if (!file || !token) return;
    setStatus("queued");
    setClips([]);
    setCurrentJobId(null);
    setError(null);

    const preset = DURATION_PRESETS[durationPreset] ?? DURATION_PRESETS.orta;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("style", style);
    formData.append("remove_fillers", String(removeFillers));
    formData.append("subtitle_color", subtitleColor);
    formData.append("subtitle_position", subtitlePosition);
    formData.append("aspect", aspect);
    if (canCustomize) {
      formData.append("clip_count", String(clipCount));
      formData.append("min_duration", String(preset.min));
      formData.append("max_duration", String(preset.max));
    }

    const res = await fetch(`${API_URL}/api/upload`, {
      method: "POST",
      headers: authHeaders(token),
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus("error");
      setError(data.detail || "Yükleme başarısız");
      return;
    }
    const jobId = data.job_id;
    setCurrentJobId(jobId);

    const poll = setInterval(async () => {
      const r = await fetch(`${API_URL}/api/jobs/${jobId}`, { headers: authHeaders(token) });
      const jobData = await r.json();
      setStatus(jobData.status);
      if (jobData.status === "done") {
        setClips(jobData.clips);
        setCurrentAspect(jobData.aspect || "9:16");
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

  const isBusy = status !== "idle" && status !== "done" && status !== "error";

  if (!token) return null;

  const limitReached = me?.usage.limit !== null && me?.usage.limit !== undefined && me.usage.used >= me.usage.limit;
  const effectiveClipCount = canCustomize ? clipCount : 5;
  const estimatedCost = renderOptions.credits.base + effectiveClipCount * renderOptions.credits.per_clip;

  return (
    <main className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0d02] to-black" />
        <ParallaxStars speed={0.6} />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-orange-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <header className="fixed top-0 left-0 w-full z-50 pt-6 px-4">
        <nav className="max-w-5xl mx-auto flex items-center justify-between gap-4 bg-black/60 backdrop-blur-xl border border-white/10 rounded-full px-6 py-3 shadow-2xl">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-5 h-5 bg-orange-500 rounded-sm rotate-45" />
            <span className="text-lg font-bold font-display tracking-tight hidden sm:inline">Klipster</span>
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
      </header>

      <div className="relative z-10 max-w-2xl mx-auto px-6 pt-32 pb-20 flex flex-col items-center text-center gap-6">
        {me && !me.user.email_verified && (
          <div className="w-full flex flex-wrap items-center justify-between gap-3 rounded-xl border border-orange-500/20 bg-orange-500/[0.06] px-4 py-3 text-left">
            <p className="text-sm text-orange-200">E-posta adresini henüz doğrulamadın.</p>
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
              className="text-xs font-semibold text-orange-400 hover:text-orange-300 transition-colors disabled:opacity-40"
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
          <p className="text-sm bg-orange-500/10 border border-orange-500/20 text-orange-300 rounded-lg px-4 py-3 w-full text-left">
            Bu ayki kredin doldu ({me?.usage.used}/{me?.usage.limit} kredi). Daha fazla video için bir üst plana geçmen gerekiyor.
          </p>
        )}

        <div className="w-full rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-8 sm:p-10 flex flex-col items-center gap-6 shadow-2xl">
          <label className="w-full flex flex-col items-center gap-3 border border-dashed border-white/15 rounded-xl px-6 py-8 cursor-pointer hover:border-orange-500/40 hover:bg-white/[0.02] transition-colors">
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

          <div className="w-full flex flex-col sm:flex-row gap-3 text-left">
            <label className="flex-1 text-xs font-medium text-zinc-400">
              Altyazı stili
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/60 transition-colors"
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
                className="h-4 w-4 accent-orange-500"
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
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/60 transition-colors"
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
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/60 transition-colors"
              >
                {renderOptions.positions.map((p) => (
                  <option key={p.id} value={p.id} className="bg-black">
                    {p.label}
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
                      ? "ring-2 ring-offset-2 ring-offset-black ring-orange-500 border-transparent"
                      : "border-white/20"
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="w-full text-left">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-zinc-400">Klip sayısı ve süresi</span>
              {!canCustomize && (
                <span className="flex items-center gap-1 text-[10px] font-semibold text-orange-400 bg-orange-500/10 border border-orange-500/20 px-2 py-0.5 rounded-full">
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
                  className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/60 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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
                  className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/60 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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
                <Link href="/#fiyatlandirma" className="text-orange-400 hover:underline">
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
            disabled={!file || isBusy || limitReached}
            className="bg-orange-500 text-black px-8 py-2.5 rounded-full font-semibold text-sm hover:bg-orange-600 transition disabled:opacity-30 disabled:hover:bg-orange-500"
          >
            Klipleri Oluştur
          </button>
        </div>

        {status !== "idle" && (
          <div className="flex items-center gap-2 text-zinc-400 text-sm">
            {isBusy && (
              <span className="h-3.5 w-3.5 rounded-full border-2 border-white/20 border-t-orange-500 animate-spin" />
            )}
            <span>{STATUS_LABELS[status]}</span>
          </div>
        )}
        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 w-full text-left">
            {error}
          </p>
        )}

        {clips.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full mt-4">
            {clips.map((clip, i) => (
              <ClipCard
                key={i}
                clip={clip}
                index={i}
                jobId={currentJobId}
                token={token}
                onUpdated={handleClipUpdated}
                aspectClass={ASPECT_CLASS[currentAspect] || ASPECT_CLASS["9:16"]}
              />
            ))}
          </div>
        )}

        {history.length > 0 && (
          <div className="w-full mt-14 text-left">
            <h2 className="font-display font-semibold text-lg mb-4">
              {me?.org ? "Ekibin geçmiş videoları" : "Geçmiş videoların"}
            </h2>
            <div className="flex flex-col divide-y divide-white/10 border border-white/10 rounded-xl overflow-hidden bg-white/[0.03] backdrop-blur-sm">
              {history.map((job) => (
                <div key={job.job_id} className="flex items-center justify-between px-4 py-3 text-sm">
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
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
