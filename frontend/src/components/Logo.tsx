import Image from "next/image";

/**
 * Klipster marka logosu (kırmızı K/play ikonu + "klipster" yazısı ALT ALTA,
 * tek bir görselde - eski logo yatay/genis bir yerlesimdi, bu yeni logo dikeye
 * yakin bir yerlesim (~1.07 en/boy orani). Arka plani seffaf (public/logo-v2.png).
 * className ile yukseklik/genislik her kullanim yerine gore ayarlanabilir
 * (nav bar vs footer gibi) - ama dikkat: logo dikeye yakin oldugu icin, eski
 * genis logoya gore ayarlanmis kucuk yukseklik degerleri (ör. h-9) "klipster"
 * yazisini okunmaz derecede kucultur; bu yuzden kullanim yerlerinde yukseklik
 * degerleri yeni orana gore yukseltildi.
 */
export default function Logo({ className = "h-10" }: { className?: string }) {
  return (
    <Image
      src="/logo-v2.png"
      alt="Klipster"
      width={673}
      height={627}
      priority
      className={`${className} w-auto`}
    />
  );
}
