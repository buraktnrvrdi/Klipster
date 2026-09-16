import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

export const metadata = {
  title: "Kullanım Koşulları - Klipster",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10">
      <h2 className="font-display text-lg font-semibold text-white">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-zinc-400">{children}</div>
    </section>
  );
}

export default function KullanimKosullariPage() {
  return (
    <main className="noir-selection min-h-screen bg-black text-white font-sans relative overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#160b02] to-black" />
        <ParallaxStars speed={0.4} />
        <div className="absolute inset-0 noir-grid" />
      </div>

      <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Logo className="h-9" />
          </Link>
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Ana sayfa
          </Link>
        </div>
      </header>

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-16">
        <h1 className="font-display text-3xl font-semibold tracking-tight">Kullanım Koşulları</h1>
        <p className="mt-2 text-sm text-zinc-500">Son güncelleme: Eylül 2026</p>

        <p className="mt-6 text-sm leading-relaxed text-zinc-400">
          Klipster&apos;a kayıt olarak veya hizmeti kullanarak aşağıdaki koşulları kabul etmiş
          olursun. Lütfen dikkatlice oku.
        </p>

        <Section title="1. Hizmetin Tanımı">
          <p>
            Klipster, yüklediğin uzun video içeriklerini yapay zeka yardımıyla analiz ederek kısa,
            dikey, altyazılı klipler haline getiren bir yazılım hizmetidir. Hizmet &quot;olduğu
            gibi&quot; (as-is) sunulur ve geliştirme aşamasındadır; zaman zaman kesintiler, hata veya
            beklenmedik davranışlar yaşanabilir.
          </p>
        </Section>

        <Section title="2. Hesap Sorumluluğun">
          <p>
            Hesabına ait şifreyi gizli tutmakla ve hesabın üzerinden yapılan tüm işlemlerden sen
            sorumlusun. 18 yaşından küçüksen ebeveyn/veli onayı olmadan hesap oluşturmamalısın.
            Hesabına ait bilgilerin başka biri tarafından ele geçirildiğini düşünüyorsan derhal
            şifreni değiştirmeli ve bize bildirmelisin.
          </p>
        </Section>

        <Section title="3. Yüklediğin İçerik">
          <p>
            Yüklediğin videoların içeriğinden tamamen sen sorumlusun. Şunları yapmayacağını kabul
            edersin:
          </p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Üzerinde hak sahibi olmadığın veya kullanım izni bulunmayan telif korumalı içerik yüklemek,</li>
            <li>Yasa dışı, nefret söylemi içeren, taciz edici veya başkalarının haklarını ihlal eden içerik yüklemek,</li>
            <li>Rızası olmayan kişilerin görüntü/sesini paylaşan içerik yüklemek,</li>
            <li>Hizmeti başka bir sistemi hacklemek, kötüye kullanmak veya aşırı yüklemek amacıyla kullanmak.</li>
          </ul>
          <p>
            Bu kurallara aykırı kullanım tespit edilirse hesabın uyarı yapılmaksızın askıya
            alınabilir veya silinebilir.
          </p>
        </Section>

        <Section title="4. Planlar, Krediler ve Ödeme">
          <p>
            Klipster; ücretsiz, Yaratıcı ve Ajans olmak üzere farklı planlar sunar. Her plan, video
            süresi ve klip sayısına göre hesaplanan aylık bir kredi kotasına sahiptir. Krediler her
            ayın başında yenilenir, bir sonraki aya devretmez. Ücretli plan ve gerçek ödeme altyapısı
            şu an geliştirme aşamasındadır; bu bölüm ödeme sistemi devreye girdiğinde
            (iptal/iade koşulları dahil) güncellenecektir.
          </p>
        </Section>

        <Section title="5. Fikri Mülkiyet">
          <p>
            Yüklediğin videolar ve bunlardan üretilen klipler üzerindeki haklar sana aittir - Klipster
            bu içerikler üzerinde, sadece sana hizmeti sunabilmek için gereken teknik işlemleri
            (işleme, geçici saklama, klip üretimi) yapma hakkına sahiptir. Klipster&apos;ın kendi
            yazılımı, tasarımı ve markası bize aittir.
          </p>
        </Section>

        <Section title="6. Ekip / Ajans Çalışma Alanları">
          <p>
            Bir ekip oluşturduğunda veya bir ekibe katıldığında, ekip sahibinin plan hakları (kredi
            limiti, klip özelleştirme) tüm ekip üyelerine paylaştırılır ve yüklenen videolar ekibin
            tüm üyeleri tarafından görülebilir hale gelir. Ekibe kimi davet edeceğinden ve ekipte
            paylaşılan içerikten ekip sahibi sorumludur.
          </p>
        </Section>

        <Section title="7. Hizmetin Sona Ermesi">
          <p>
            Hesabını istediğin zaman profil sayfandan kalıcı olarak silebilirsin - bu işlem tüm
            verilerini ve video/klip dosyalarını geri döndürülemez şekilde siler. Kullanım
            koşullarını ihlal etmen durumunda hesabını askıya alma veya sonlandırma hakkımızı saklı
            tutarız.
          </p>
        </Section>

        <Section title="8. Sorumluluğun Sınırlandırılması">
          <p>
            Klipster, yapay zeka tarafından üretilen klip/altyazı içeriğinin doğruluğunu veya
            belirli bir platformda &quot;viral&quot; olacağını garanti etmez. Hizmet geliştirme
            aşamasında olduğundan, veri kaybı veya kesinti riskine karşı önemli videolarının bir
            kopyasını kendi cihazında da saklamanı öneririz.
          </p>
        </Section>

        <Section title="9. Değişiklikler ve İletişim">
          <p>
            Bu koşulları zaman zaman güncelleyebiliriz, önemli değişikliklerde sayfanın en üstündeki
            tarihi güncelleriz. Sorularınız için{" "}
            <Link href="/iletisim" className="text-orange-400 hover:underline">
              iletişim sayfamızdan
            </Link>{" "}
            bize ulaşabilirsin.
          </p>
        </Section>
      </div>
    </main>
  );
}
