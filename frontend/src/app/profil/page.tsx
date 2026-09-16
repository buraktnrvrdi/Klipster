"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, ArrowUpRight, Check, Copy, KeyRound, LogOut, Mail, Trash2, UserPlus, Users } from "lucide-react";
import { AVATAR_META, AvatarBadge } from "@/components/AvatarIcons";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Me = {
  user: {
    id: number;
    email: string;
    plan: string;
    display_name: string | null;
    avatar: string | null;
    email_verified: boolean;
  };
  usage: { used: number; limit: number | null; unit?: string };
  effective_plan?: string;
  org?: { id: string; name: string; role: string } | null;
};

type OrgMember = {
  id: number;
  email: string;
  display_name: string | null;
  avatar: string | null;
  role: string;
};

type OrgInvite = { token: string; email: string; created_at: string };

type OrgDetail = {
  id: string;
  name: string;
  role: string;
  members: OrgMember[];
  invites: OrgInvite[];
};

const PLAN_LABELS: Record<string, string> = {
  ucretsiz: "Ücretsiz",
  yaratici: "Yaratıcı",
  ajans: "Ajans",
};

const NEXT_PLAN: Record<string, string> = {
  ucretsiz: "yaratici",
  yaratici: "ajans",
};

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export default function ProfilPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [avatars, setAvatars] = useState<string[]>([]);
  const [displayName, setDisplayName] = useState("");
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [deleteConfirming, setDeleteConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

  const [org, setOrg] = useState<OrgDetail | null>(null);
  const [orgLoaded, setOrgLoaded] = useState(false);
  const [orgName, setOrgName] = useState("");
  const [orgCreating, setOrgCreating] = useState(false);
  const [orgError, setOrgError] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [leaving, setLeaving] = useState(false);

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
      .then((data: Me) => {
        setMe(data);
        setDisplayName(data.user.display_name ?? "");
        setSelectedAvatar(data.user.avatar);
      })
      .catch(() => {
        localStorage.removeItem("klipster_token");
        router.push("/giris");
      });

    fetch(`${API_URL}/api/avatars`)
      .then((r) => r.json())
      .then(setAvatars)
      .catch(() => {});

    refreshOrg(token);
  }, [token, router]);

  function refreshOrg(t: string) {
    fetch(`${API_URL}/api/org`, { headers: authHeaders(t) })
      .then((r) => r.json())
      .then((data: { org: OrgDetail | null }) => setOrg(data.org))
      .catch(() => {})
      .finally(() => setOrgLoaded(true));
  }

  async function handleCreateOrg() {
    if (!token) return;
    setOrgError(null);
    setOrgCreating(true);
    try {
      const res = await fetch(`${API_URL}/api/org`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ name: orgName }),
      });
      const data = await res.json();
      if (!res.ok) {
        setOrgError(data.detail || "Ekip oluşturulamadı");
        return;
      }
      setOrgName("");
      refreshOrg(token);
    } catch {
      setOrgError("Sunucuya ulaşılamadı");
    } finally {
      setOrgCreating(false);
    }
  }

  async function handleInvite() {
    if (!token) return;
    setInviteError(null);
    setInviting(true);
    try {
      const res = await fetch(`${API_URL}/api/org/invite`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ email: inviteEmail }),
      });
      const data = await res.json();
      if (!res.ok) {
        setInviteError(data.detail || "Davet gönderilemedi");
        return;
      }
      setInviteEmail("");
      refreshOrg(token);
    } catch {
      setInviteError("Sunucuya ulaşılamadı");
    } finally {
      setInviting(false);
    }
  }

  async function handleCancelInvite(inviteToken: string) {
    if (!token) return;
    try {
      await fetch(`${API_URL}/api/org/invites/${inviteToken}`, {
        method: "DELETE",
        headers: authHeaders(token),
      });
      refreshOrg(token);
    } catch {
      // sessizce yoksay
    }
  }

  async function handleRemoveMember(memberId: number) {
    if (!token) return;
    try {
      await fetch(`${API_URL}/api/org/members/${memberId}`, {
        method: "DELETE",
        headers: authHeaders(token),
      });
      refreshOrg(token);
    } catch {
      // sessizce yoksay
    }
  }

  async function handleLeaveOrg() {
    if (!token) return;
    setLeaving(true);
    try {
      await fetch(`${API_URL}/api/org/leave`, {
        method: "POST",
        headers: authHeaders(token),
      });
      refreshOrg(token);
    } catch {
      // sessizce yoksay
    } finally {
      setLeaving(false);
    }
  }

  async function handleResendVerification() {
    if (!token) return;
    setResending(true);
    try {
      await fetch(`${API_URL}/api/auth/resend-verification`, {
        method: "POST",
        headers: authHeaders(token),
      });
      setResent(true);
      setTimeout(() => setResent(false), 4000);
    } catch {
      // sessizce yoksay
    } finally {
      setResending(false);
    }
  }

  function copyInviteLink(inviteToken: string) {
    const link = `${window.location.origin}/davet?token=${inviteToken}`;
    navigator.clipboard?.writeText(link).then(() => {
      setCopiedToken(inviteToken);
      setTimeout(() => setCopiedToken(null), 2000);
    });
  }

  async function handleSave() {
    if (!token) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/auth/profile`, {
        method: "PATCH",
        headers: authHeaders(token),
        body: JSON.stringify({ display_name: displayName, avatar: selectedAvatar }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Güncellenemedi");
        return;
      }
      setMe((prev) => (prev ? { ...prev, user: data.user } : prev));
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Sunucuya ulaşılamadı");
    } finally {
      setSaving(false);
    }
  }

  async function handleChangePassword() {
    if (!token) return;
    setPasswordError(null);
    setPasswordSaved(false);
    if (newPassword.length < 6) {
      setPasswordError("Yeni şifre en az 6 karakter olmalı");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("Yeni şifreler eşleşmiyor");
      return;
    }
    setPasswordSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/change-password`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      const data = await res.json();
      if (!res.ok) {
        setPasswordError(data.detail || "Şifre değiştirilemedi");
        return;
      }
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordSaved(true);
      setTimeout(() => setPasswordSaved(false), 2500);
    } catch {
      setPasswordError("Sunucuya ulaşılamadı");
    } finally {
      setPasswordSaving(false);
    }
  }

  async function handleDeleteAccount() {
    if (!token) return;
    setDeleteError(null);
    setDeleting(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/account`, {
        method: "DELETE",
        headers: authHeaders(token),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setDeleteError(data.detail || "Hesap silinemedi");
        return;
      }
      localStorage.removeItem("klipster_token");
      router.push("/");
    } catch {
      setDeleteError("Sunucuya ulaşılamadı");
    } finally {
      setDeleting(false);
    }
  }

  if (!token || !me) return null;

  const previewName = displayName.trim() || me.user.email.split("@")[0];

  return (
    <main className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#160202] to-black" />
        <ParallaxStars speed={0.4} />
        <div className="absolute top-0 left-0 w-[600px] h-[600px] bg-red-600/10 rounded-full blur-[140px] -translate-x-1/3 -translate-y-1/3" />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Logo className="h-14" />
          </Link>
          <Link
            href="/app"
            className="flex items-center gap-1.5 text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Panele dön
          </Link>
        </div>
      </header>

      <div className="relative z-10 max-w-4xl mx-auto px-6 py-14">
        <h1 className="font-display text-3xl font-semibold tracking-tight">Profilim</h1>
        <p className="mt-1.5 text-sm text-zinc-400">
          Hesap görünümünü kendine göre düzenle: görünen isim ve avatarını buradan yönet.
        </p>

        {!me.user.email_verified && (
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3">
            <div className="flex items-center gap-2.5">
              <Mail className="h-4 w-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-200">
                E-posta adresini henüz doğrulamadın — gelen kutunu kontrol et.
              </p>
            </div>
            <button
              onClick={handleResendVerification}
              disabled={resending}
              className="text-xs font-semibold text-red-400 hover:text-red-300 transition-colors disabled:opacity-40"
            >
              {resent ? "Gönderildi ✓" : resending ? "Gönderiliyor..." : "Doğrulama e-postasını tekrar gönder"}
            </button>
          </div>
        )}

        <div className="mt-10 grid md:grid-cols-[260px_1fr] gap-6 items-start">
          {/* Onizleme karti */}
          <div className="md:sticky md:top-24 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 flex flex-col items-center text-center gap-3 shadow-2xl">
            <AvatarBadge id={selectedAvatar} size={72} />
            <div>
              <p className="font-display font-semibold text-lg leading-tight">{previewName}</p>
              <p className="text-xs text-zinc-500 mt-1 break-all">{me.user.email}</p>
            </div>
            <span className="inline-block text-xs font-semibold text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-1 rounded-full">
              {PLAN_LABELS[me.user.plan] ?? me.user.plan} plan
            </span>

            {/* Kredi kullanim ozeti */}
            <div className="w-full mt-2 pt-4 border-t border-white/10 text-left">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Bu ay kullanılan kredi</span>
                <span className="text-zinc-200 font-medium">
                  {me.usage.used}/{me.usage.limit ?? "∞"}
                </span>
              </div>
              {me.usage.limit !== null && (
                <div className="mt-2 h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-red-500 transition-all"
                    style={{
                      width: `${Math.min(100, (me.usage.used / Math.max(1, me.usage.limit)) * 100)}%`,
                    }}
                  />
                </div>
              )}
              <p className="mt-2 text-[11px] text-zinc-500">Krediler her ayın başında yenilenir.</p>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            {/* Isim */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6">
              <label className="block mb-2 text-sm font-medium text-zinc-300">Görünen isim</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                maxLength={24}
                placeholder="Nasıl görünmek istersin?"
                className="w-full max-w-[240px] bg-black/40 border border-white/10 rounded-lg px-3.5 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
              />
              <p className="mt-1.5 text-xs text-zinc-500">En fazla 24 karakter. Boş bırakırsan e-postan gösterilir.</p>
            </div>

            {/* Avatar secimi */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6">
              <label className="text-sm font-medium text-zinc-300">Avatar seç</label>
              <div className="mt-3 grid grid-cols-4 sm:grid-cols-8 gap-3">
                {avatars.map((a) => (
                  <button
                    key={a}
                    onClick={() => setSelectedAvatar(a)}
                    className={`relative h-14 w-14 rounded-xl flex items-center justify-center border-2 transition-all ${
                      selectedAvatar === a
                        ? "border-red-500 scale-105"
                        : "border-transparent hover:border-white/20"
                    }`}
                    style={{ background: AVATAR_META[a] ? "transparent" : undefined }}
                  >
                    <AvatarBadge id={a} size={44} />
                    {selectedAvatar === a && (
                      <span className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-red-500 text-black flex items-center justify-center">
                        <Check className="h-3 w-3" />
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 max-w-sm">
                {error}
              </p>
            )}

            <div className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-red-500 text-black px-6 py-2.5 rounded-full font-semibold text-sm hover:bg-red-600 transition disabled:opacity-40"
              >
                {saving ? "Kaydediliyor..." : "Kaydet"}
              </button>
              {saved && <span className="text-sm text-green-400 font-medium">Kaydedildi ✓</span>}
            </div>

            {/* Plan yonetimi */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 flex items-center justify-between gap-4 flex-wrap">
              <div>
                <p className="text-sm font-medium text-zinc-300">Planın</p>
                <p className="mt-1 text-lg font-display font-semibold">
                  {PLAN_LABELS[me.user.plan] ?? me.user.plan}
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {NEXT_PLAN[me.user.plan]
                    ? "Daha fazla kredi ve klip özelleştirme için yükselt."
                    : "En üst plandasın — sınırsız kredi."}
                </p>
              </div>
              {NEXT_PLAN[me.user.plan] && (
                <Link
                  href="/#fiyatlandirma"
                  className="flex items-center gap-1.5 bg-white/5 border border-white/10 hover:border-red-500/40 hover:text-red-400 text-zinc-200 px-4 py-2 rounded-full text-sm font-medium transition-colors"
                >
                  Planları incele
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              )}
            </div>

            {/* Hesap guvenligi */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6">
              <div className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-zinc-500" />
                <label className="text-sm font-medium text-zinc-300">Şifreni değiştir</label>
              </div>
              <div className="mt-3 flex flex-col gap-3 max-w-sm">
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Mevcut şifre"
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Yeni şifre (en az 6 karakter)"
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Yeni şifre (tekrar)"
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                />
              </div>
              {passwordError && (
                <p className="mt-3 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 max-w-sm">
                  {passwordError}
                </p>
              )}
              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={handleChangePassword}
                  disabled={passwordSaving || !currentPassword || !newPassword}
                  className="bg-white/10 hover:bg-white/15 text-white px-6 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
                >
                  {passwordSaving ? "Değiştiriliyor..." : "Şifreyi değiştir"}
                </button>
                {passwordSaved && <span className="text-sm text-green-400 font-medium">Değiştirildi ✓</span>}
              </div>
            </div>

            {/* Ekip / Ajans isbirligi - Ajans plani sahiplerine ve davetli tum uyelere gorunur */}
            {orgLoaded && (me.user.plan === "ajans" || org) && (
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-zinc-500" />
                  <label className="text-sm font-medium text-zinc-300">Ekip</label>
                </div>

                {!org ? (
                  <>
                    <p className="mt-2 text-xs text-zinc-500 max-w-md">
                      Bir ekip oluştur, video/klip geçmişini ve kredi hakkını ekibinle paylaş.
                    </p>
                    <div className="mt-4 flex flex-wrap items-center gap-3 max-w-sm">
                      <input
                        type="text"
                        value={orgName}
                        onChange={(e) => setOrgName(e.target.value)}
                        placeholder="Ekip adı (opsiyonel)"
                        className="flex-1 min-w-[180px] bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                      />
                      <button
                        onClick={handleCreateOrg}
                        disabled={orgCreating}
                        className="bg-red-500 text-black px-5 py-2.5 rounded-full font-semibold text-sm hover:bg-red-600 transition disabled:opacity-40"
                      >
                        {orgCreating ? "Oluşturuluyor..." : "Ekip oluştur"}
                      </button>
                    </div>
                    {orgError && (
                      <p className="mt-3 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 max-w-sm">
                        {orgError}
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p className="mt-1 text-lg font-display font-semibold">{org.name}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {org.role === "owner"
                        ? "Ekip sahibisin — üyeler senin plan haklarını kullanır."
                        : "Bu ekibin üyesisin — ekip sahibinin plan haklarını kullanıyorsun."}
                    </p>

                    <div className="mt-4 flex flex-col gap-2">
                      {org.members.map((m) => (
                        <div
                          key={m.id}
                          className="flex items-center justify-between gap-3 bg-black/30 border border-white/10 rounded-lg px-3.5 py-2.5"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <AvatarBadge id={m.avatar} size={28} />
                            <div className="min-w-0">
                              <p className="text-sm text-zinc-200 truncate">
                                {m.display_name || m.email.split("@")[0]}
                              </p>
                              <p className="text-[11px] text-zinc-500 truncate">{m.email}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[11px] font-medium text-zinc-400 bg-white/5 px-2 py-0.5 rounded-full">
                              {m.role === "owner" ? "Sahip" : "Üye"}
                            </span>
                            {org.role === "owner" && m.role !== "owner" && (
                              <button
                                onClick={() => handleRemoveMember(m.id)}
                                title="Üyeyi çıkar"
                                className="text-zinc-500 hover:text-red-400 transition-colors"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {org.role === "owner" && (
                      <>
                        <div className="mt-4 pt-4 border-t border-white/10">
                          <div className="flex items-center gap-2 text-xs text-zinc-400 mb-2">
                            <UserPlus className="h-3.5 w-3.5" />
                            E-posta ile davet et
                          </div>
                          <div className="flex flex-wrap items-center gap-3 max-w-sm">
                            <input
                              type="email"
                              value={inviteEmail}
                              onChange={(e) => setInviteEmail(e.target.value)}
                              placeholder="ornek@eposta.com"
                              className="flex-1 min-w-[180px] bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-red-500/60 transition-colors"
                            />
                            <button
                              onClick={handleInvite}
                              disabled={inviting || !inviteEmail}
                              className="bg-white/10 hover:bg-white/15 text-white px-5 py-2.5 rounded-full font-semibold text-sm transition disabled:opacity-40"
                            >
                              {inviting ? "Gönderiliyor..." : "Davet et"}
                            </button>
                          </div>
                          {inviteError && (
                            <p className="mt-3 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 max-w-sm">
                              {inviteError}
                            </p>
                          )}
                        </div>

                        {org.invites.length > 0 && (
                          <div className="mt-4 flex flex-col gap-2">
                            <p className="text-xs text-zinc-500">Bekleyen davetler</p>
                            {org.invites.map((inv) => (
                              <div
                                key={inv.token}
                                className="flex items-center justify-between gap-3 bg-black/30 border border-white/10 rounded-lg px-3.5 py-2.5"
                              >
                                <span className="text-sm text-zinc-300 truncate">{inv.email}</span>
                                <div className="flex items-center gap-3 shrink-0">
                                  <button
                                    onClick={() => copyInviteLink(inv.token)}
                                    className="flex items-center gap-1 text-xs text-zinc-400 hover:text-red-400 transition-colors"
                                  >
                                    <Copy className="h-3 w-3" />
                                    {copiedToken === inv.token ? "Kopyalandı ✓" : "Linki kopyala"}
                                  </button>
                                  <button
                                    onClick={() => handleCancelInvite(inv.token)}
                                    title="Daveti iptal et"
                                    className="text-zinc-500 hover:text-red-400 transition-colors"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    )}

                    {org.role !== "owner" && (
                      <div className="mt-4 pt-4 border-t border-white/10">
                        <button
                          onClick={handleLeaveOrg}
                          disabled={leaving}
                          className="flex items-center gap-1.5 text-zinc-400 hover:text-red-400 text-sm font-medium transition-colors disabled:opacity-40"
                        >
                          <LogOut className="h-3.5 w-3.5" />
                          {leaving ? "Ayrılıyor..." : "Ekipten ayrıl"}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Tehlikeli bolge */}
            <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.03] backdrop-blur-xl p-6">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400" />
                <label className="text-sm font-medium text-red-300">Hesabımı sil</label>
              </div>
              <p className="mt-2 text-xs text-zinc-500 max-w-md">
                Hesabını sildiğinde e-postan, tüm video/klip geçmişin ve dosyaların kalıcı olarak
                silinir. Bu işlem geri alınamaz.
              </p>
              {deleteError && (
                <p className="mt-3 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 max-w-sm">
                  {deleteError}
                </p>
              )}
              <div className="mt-4 flex items-center gap-3">
                {!deleteConfirming ? (
                  <button
                    onClick={() => setDeleteConfirming(true)}
                    className="text-red-400 border border-red-500/30 hover:bg-red-500/10 px-5 py-2 rounded-full text-sm font-medium transition-colors"
                  >
                    Hesabımı sil
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleDeleteAccount}
                      disabled={deleting}
                      className="bg-red-500 hover:bg-red-600 text-black px-5 py-2 rounded-full text-sm font-semibold transition disabled:opacity-40"
                    >
                      {deleting ? "Siliniyor..." : "Evet, kalıcı olarak sil"}
                    </button>
                    <button
                      onClick={() => setDeleteConfirming(false)}
                      className="text-zinc-400 hover:text-white text-sm font-medium transition-colors"
                    >
                      Vazgeç
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
