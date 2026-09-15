import Image from "next/image";

/**
 * Klipster marka logosu (turuncu K ikonu + "KLIPSTER" yazısı tek bir görselde).
 * Eskiden ayrı ayrı bir turuncu kare (icon) + <span>Klipster</span> olarak
 * elle çiziliyordu - artık tasarımdan gelen tek bir PNG kullanılıyor
 * (public/logo.png, arka planı şeffaf). className ile yükseklik/genişlik
 * her kullanım yerine göre ayarlanabilir (nav bar vs footer gibi).
 */
export default function Logo({ className = "h-5" }: { className?: string }) {
  return (
    <Image
      src="/logo.png"
      alt="Klipster"
      width={757}
      height={242}
      priority
      className={`${className} w-auto`}
    />
  );
}
