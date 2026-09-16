"use client";

// Adobe Firefly ile uretilen, yazisiz "slime -> telefon" videosu, koyu
// (noir) temaya uygun cam efektli bir cerceve icinde sunuluyor. Metin
// videonun USTUNDE, ayri bir baslik olarak duruyor - boylece hem her zaman
// keskin/dogru cikiyor hem de videonun kendi goruntusuyle cakismiyor.

export default function SlimePhone() {
  return (
    <div className="flex flex-col items-center">
      <p className="animate-fade-up relative z-10 font-display font-bold text-xl sm:text-2xl text-center tracking-tight mb-10 leading-relaxed">
        <span className="text-white">Videonu </span>
        <span className="text-red-500">popüler kliplere</span>
        <span className="text-white"> çevir!</span>
      </p>

      <div className="relative">
        {/* ambient glow behind the glass card */}
        <div
          className="absolute -inset-x-6 top-4 bottom-[-1.5rem] -z-10 rounded-[3rem] blur-3xl opacity-60"
          style={{
            background:
              "radial-gradient(circle, rgba(239,68,68,0.45), transparent 70%)",
          }}
        />

        {/* glass frame */}
        <div className="relative rounded-[2.5rem] border border-white/15 bg-white/5 backdrop-blur-xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.6)] p-3">
          <div className="w-full max-w-[260px] rounded-[2rem] overflow-hidden bg-black ring-1 ring-white/10">
            <video
              src="/phone-slime.mp4"
              autoPlay
              muted
              loop
              playsInline
              className="w-full h-full object-cover aspect-[9/16]"
            />
          </div>
          {/* subtle glass highlight */}
          <div className="pointer-events-none absolute inset-0 rounded-[2.5rem] bg-gradient-to-br from-white/10 via-transparent to-transparent" />
        </div>
      </div>
    </div>
  );
}
