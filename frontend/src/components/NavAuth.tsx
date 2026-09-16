"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ChevronDown, LogOut, LayoutDashboard, UserRound, ArrowRight } from "lucide-react";
import { AvatarBadge } from "@/components/AvatarIcons";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Me = {
  user: { id: number; email: string; plan: string; display_name: string | null; avatar: string | null };
};

const PLAN_LABELS: Record<string, string> = {
  ucretsiz: "Ücretsiz",
  yaratici: "Yaratıcı",
  ajans: "Ajans",
};

export default function NavAuth() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("klipster_token");
    if (!token) {
      setLoading(false);
      return;
    }
    fetch(`${API_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async (r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(setMe)
      .catch(() => localStorage.removeItem("klipster_token"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleLogout() {
    localStorage.removeItem("klipster_token");
    setMe(null);
    setOpen(false);
    window.location.href = "/";
  }

  if (loading) {
    return <div className="h-9 w-24 rounded-full bg-white/5 border border-white/10 animate-pulse" />;
  }

  if (!me) {
    return (
      <div className="flex items-center gap-4">
        <Link
          href="/giris"
          className="hidden md:block text-sm font-medium text-zinc-300 hover:text-white transition-colors"
        >
          Giriş yap
        </Link>
        <Link
          href="/kayit"
          className="group relative inline-flex items-center justify-center overflow-hidden rounded-full bg-white/5 px-6 py-2 transition-transform active:scale-95"
        >
          <span className="absolute inset-0 border border-white/10 rounded-full" />
          <span className="absolute inset-[-100%] animate-[spin_3s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,transparent_75%,#ef4444_100%)] opacity-0 group-hover:opacity-100 transition-opacity" />
          <span className="absolute inset-[1px] rounded-full bg-black" />
          <span className="relative z-10 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white">
            Üye ol <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          </span>
        </Link>
      </div>
    );
  }

  const displayName = me.user.display_name?.trim() || me.user.email.split("@")[0];

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 pl-1.5 pr-3 py-1.5 rounded-full border border-white/10 bg-white/5 hover:border-white/20 transition-colors"
      >
        <AvatarBadge id={me.user.avatar} size={28} />
        <span className="text-sm font-medium text-zinc-200 hidden sm:inline max-w-[140px] truncate">
          {displayName}
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-zinc-500 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-black border border-white/10 rounded-xl shadow-2xl py-1.5 z-50">
          <div className="px-3.5 py-2.5 border-b border-white/10 flex items-center gap-2.5">
            <AvatarBadge id={me.user.avatar} size={36} />
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{displayName}</p>
              <p className="text-xs text-zinc-500 mt-0.5">
                {PLAN_LABELS[me.user.plan] ?? me.user.plan} plan
              </p>
            </div>
          </div>
          <Link
            href="/profil"
            className="flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white transition-colors"
            onClick={() => setOpen(false)}
          >
            <UserRound className="h-4 w-4 text-zinc-500" />
            Profilim
          </Link>
          <Link
            href="/app"
            className="flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white transition-colors"
            onClick={() => setOpen(false)}
          >
            <LayoutDashboard className="h-4 w-4 text-zinc-500" />
            Panele git
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors text-left"
          >
            <LogOut className="h-4 w-4" />
            Çıkış yap
          </button>
        </div>
      )}
    </div>
  );
}
