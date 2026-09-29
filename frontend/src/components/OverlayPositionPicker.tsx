"use client";

import { useCallback, useRef } from "react";

// backend/app/services/video.py ASPECT_PRESETS ile birebir ayni oranlar -
// onizlemenin kutusu, gercek cikti karesiyle ayni en-boy oranina sahip olsun diye.
const ASPECT_RATIOS: Record<string, number> = {
  "9:16": 9 / 16,
  "4:5": 4 / 5,
  "1:1": 1,
};

// backend/app/services/video.py OVERLAY_SCALES ile birebir ayni degerler.
const OVERLAY_WIDTH_RATIOS: Record<string, number> = {
  kucuk: 0.15,
  orta: 0.22,
  buyuk: 0.3,
};

type Props = {
  previewUrl: string;
  aspect: string;
  scale: string;
  x: number;
  y: number;
  onChange: (x: number, y: number) => void;
};

export default function OverlayPositionPicker({ previewUrl, aspect, scale, x, y, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);

  const widthRatio = OVERLAY_WIDTH_RATIOS[scale] ?? OVERLAY_WIDTH_RATIOS.orta;
  const ratio = ASPECT_RATIOS[aspect] ?? ASPECT_RATIOS["9:16"];

  const updateFromPointer = useCallback(
    (clientX: number, clientY: number) => {
      const el = containerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const nx = (clientX - rect.left) / rect.width;
      const ny = (clientY - rect.top) / rect.height;
      onChange(Math.min(Math.max(nx, 0), 1), Math.min(Math.max(ny, 0), 1));
    },
    [onChange]
  );

  const handlePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    (e.target as Element).setPointerCapture(e.pointerId);
    updateFromPointer(e.clientX, e.clientY);
  };
  const handlePointerMove = (e: React.PointerEvent) => {
    if (!draggingRef.current) return;
    updateFromPointer(e.clientX, e.clientY);
  };
  const handlePointerUp = (e: React.PointerEvent) => {
    draggingRef.current = false;
    try {
      (e.target as Element).releasePointerCapture(e.pointerId);
    } catch {
      // yakalama zaten birakilmis olabilir - yoksayilabilir.
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full max-w-[160px] bg-black/50 border border-white/10 rounded-lg overflow-hidden touch-none select-none cursor-crosshair"
      style={{ aspectRatio: `${ratio}` }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={previewUrl}
        alt="Logo konumu"
        draggable={false}
        className="absolute pointer-events-none rounded-sm shadow"
        style={{
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          width: `${widthRatio * 100}%`,
          height: "auto",
        }}
      />
    </div>
  );
}
