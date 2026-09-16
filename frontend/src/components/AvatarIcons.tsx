"use client";

import type { CSSProperties, ReactElement } from "react";

// Klipster'a ozel, elle cizilmis basit geometrik avatar ikon seti.
// Bilinen bir emoji/ikon kutuphanesinden degil - markaya ait, kendi
// cizdigimiz sade SVG isaretler. Her birinin kendi rozet rengi var.

type IconProps = { className?: string; style?: CSSProperties };

function Bolt({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <polygon points="13,2 4,14 11,14 9,22 20,9 12,9" />
    </svg>
  );
}

function Flame({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <path d="M12 2c1 3-3 4-3 8a3 3 0 006 0c1 1 1.5 2.5 1.5 4a4.5 4.5 0 01-9 0C7.5 9 12 7 12 2z" />
    </svg>
  );
}

function Spark({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <path d="M12 2c0.8 4.5 3.5 7.2 8 8-4.5 0.8-7.2 3.5-8 8-0.8-4.5-3.5-7.2-8-8 4.5-0.8 7.2-3.5 8-8z" />
    </svg>
  );
}

function Comet({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <circle cx="17" cy="7" r="3.2" />
      <path d="M15 9 3 21l3-8 3 3 2-3 2 2z" opacity="0.55" />
    </svg>
  );
}

function ClipMark({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="none" stroke="white" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round">
      <rect x="4" y="6" width="16" height="14" rx="3" />
      <path d="M4 10h16" />
      <path d="M8 6l2-3M16 6l-2-3" />
      <polygon points="10.5,13 10.5,17 14.5,15" fill="white" stroke="none" />
    </svg>
  );
}

function Wave({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <rect x="2" y="9" width="3" height="6" rx="1.5" />
      <rect x="7.5" y="5" width="3" height="14" rx="1.5" />
      <rect x="13" y="2" width="3" height="20" rx="1.5" />
      <rect x="18.5" y="7" width="3" height="10" rx="1.5" />
    </svg>
  );
}

function Gem({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <polygon points="12,2 20,9 12,22 4,9" />
    </svg>
  );
}

function Crown({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <polygon points="3,8 8,12 12,4 16,12 21,8 19,18 5,18" />
    </svg>
  );
}

function Rocket({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <path d="M12 2c3 2 4.5 5.5 4.5 9.5 0 2-0.6 3.8-1.2 5l-3.3 3.5-3.3-3.5c-0.6-1.2-1.2-3-1.2-5C7.5 7.5 9 4 12 2z" />
      <circle cx="12" cy="10.5" r="1.8" fill="#0a0a0a" />
      <polygon points="7.5,15 4,17 5.5,12" opacity="0.6" />
      <polygon points="16.5,15 20,17 18.5,12" opacity="0.6" />
    </svg>
  );
}

function Shield({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z" />
    </svg>
  );
}

function Infinity({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round">
      <path d="M7 9a3.5 3.5 0 000 7c2.5 0 3.5-2.5 5-4.5s2.5-2.5 5-2.5a3.5 3.5 0 010 7c-2.5 0-3.5-2.5-5-4.5S9.5 9 7 9z" />
    </svg>
  );
}

function Moon({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="white">
      <path d="M15 3a9 9 0 100 18 7 7 0 010-18z" />
    </svg>
  );
}

function Sun({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4.5" fill="white" stroke="none" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
        <line
          key={deg}
          x1="12"
          y1="3.5"
          x2="12"
          y2="1.5"
          transform={`rotate(${deg} 12 12)`}
        />
      ))}
    </svg>
  );
}

function Target({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="none" stroke="white" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.4" fill="white" stroke="none" />
    </svg>
  );
}

function Pulse({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="2,13 7,13 9,7 13,19 15,13 22,13" />
    </svg>
  );
}

function Orbit({ className, style }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style} fill="none" stroke="white" strokeWidth="2">
      <circle cx="12" cy="12" r="2.2" fill="white" stroke="none" />
      <ellipse cx="12" cy="12" rx="10" ry="4.2" />
      <ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(60 12 12)" />
    </svg>
  );
}

export const AVATAR_META: Record<string, { bg: string; Icon: (p: IconProps) => ReactElement }> = {
  bolt: { bg: "#ef4444", Icon: Bolt },
  flame: { bg: "#dc2626", Icon: Flame },
  spark: { bg: "#f87171", Icon: Spark },
  comet: { bg: "#18181b", Icon: Comet },
  clip: { bg: "#1c1917", Icon: ClipMark },
  wave: { bg: "#b91c1c", Icon: Wave },
  gem: { bg: "#991b1b", Icon: Gem },
  crown: { bg: "#b45309", Icon: Crown },
  rocket: { bg: "#27272a", Icon: Rocket },
  shield: { bg: "#ef4444", Icon: Shield },
  infinity: { bg: "#292524", Icon: Infinity },
  moon: { bg: "#3f3f46", Icon: Moon },
  sun: { bg: "#f59e0b", Icon: Sun },
  target: { bg: "#dc2626", Icon: Target },
  pulse: { bg: "#dc2626", Icon: Pulse },
  orbit: { bg: "#18181b", Icon: Orbit },
};

export const AVATAR_KEYS = Object.keys(AVATAR_META);

export function AvatarBadge({ id, size = 32 }: { id: string | null; size?: number }) {
  const meta = id ? AVATAR_META[id] : null;
  if (!meta) {
    return (
      <span
        className="rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-red-600 shrink-0"
        style={{ width: size, height: size }}
      >
        <svg viewBox="0 0 24 24" width={size * 0.5} height={size * 0.5} fill="currentColor">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7" />
        </svg>
      </span>
    );
  }
  const { bg, Icon } = meta;
  return (
    <span
      className="rounded-full flex items-center justify-center shrink-0"
      style={{ width: size, height: size, background: bg }}
    >
      <Icon className="block" style={{ width: size * 0.55, height: size * 0.55 }} />
    </span>
  );
}
