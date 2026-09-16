import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import ParallaxStars from "@/components/ParallaxStars";
import Logo from "@/components/Logo";

export const metadata = {
  title: "Gizlilik Politikası ve KVKK Aydınlatma Metni - Klipster",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10">
      <h2 className="font-display text-lg font-semibold text-white">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-zinc-400">{children}</div>
    </section>
  );
}

export default function GizlilikPolitikasiPage() {
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
        <h1 className="font-display text-3xl font-semibold tracking-tight">
          Gizlilik Politikası ve KVKK Aydınlatma Metni
        </h1>
        <p className="mt-2 text-sm text-zinc-500">Son güncelleme: Eylül 2026</p>

        <p className="mt-6 text-sm leading-relaxed text-zinc-400">
          Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu (&quot;KVKK&quot;) kapsamında,
          Klipster (&quot;biz&quot;, &quot;hizmet&quot;) tarafından işlenen kişisel verileriniz hakkında
          sizi bilgilendirmek amacıyla hazırlanmıştır.
        </p>

        <Section title="1. Veri Sorumlusu">
          <p>
            Klipster hizmeti şu an için şahıs bünyesinde, Burak tarafından işletilmektedir (şirket
            kuruluş süreci devam etmektedir - bu bölüm resmi bir şirket kurulduğunda güncellenecektir).
            Kişisel verilerinizle ilgili sorularınız için{" "}
            <a href="mailto:brightnotedestek@gmail.com" className="text-orange-400 hover:underline">
              brightnotedestek@gmail.com
            </a>{" "}
            adresinden bize ulaşabilirsiniz.
          </p>
        </Section>

        <Section title="2. Toplanan Kişisel Veriler">
          <p>Hizmeti kullanırken aşağıdaki verileri topluyoruz:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Kimlik/iletişim verisi: e-posta adresin, (varsa) belirlediğin görünen isim ve avatar seçimin.</li>
            <li>Hesap güvenliği verisi: şifrenin geri döndürülemez şekilde şifrelenmiş (hash&apos;lenmiş) hali - şifrenin kendisi hiçbir zaman düz metin olarak saklanmaz.</li>
            <li>İçerik verisi: yüklediğin video dosyaları, bu videolardan çıkarılan konuşma metni (transkript), oluşturulan klipler ve altyazılar.</li>
            <li>Kullanım verisi: aylık kredi tüketimin, plan bilgin, oluşturduğun iş (job) kayıtları ve zaman damgaları.</li>
            <li>Ekip verisi: bir ekip/ajans çalışma alanı oluşturursan veya bir ekibe katılırsan, ekip üyeliği ve rolün (sahip/üye).</li>
            <li>Teknik veri: oturum jetonu (token) ve oturumun geçerlilik süresi - IP adresin veritabanında ayrıca saklanmaz.</li>
          </ul>
        </Section>

        <Section title="3. Verilerin İşlenme Amaçları ve Hukuki Sebebi">
          <p>
            Verilerin şu amaçlarla işlenmesi, KVKK madde 5/2 kapsamında &quot;bir sözleşmenin
            kurulması veya ifasıyla doğrudan doğruya ilgili olması&quot; ve &quot;veri sorumlusunun
            meşru menfaati&quot; hukuki sebeplerine dayanmaktadır:
          </p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Hesabını oluşturmak, kimliğini doğrulamak ve oturumunu yönetmek.</li>
            <li>Yüklediğin videoyu işleyip senin için klip ve altyazı üretmek (hizmetin temel amacı).</li>
            <li>Plan/kredi limitlerini doğru şekilde uygulamak ve kullanım geçmişini göstermek.</li>
            <li>Hesap güvenliğini sağlamak (şifre sıfırlama, e-posta doğrulama, şüpheli oturumları sonlandırma).</li>
            <li>Yasal yükümlülüklerimizi yerine getirmek ve hizmeti kötüye kullanıma karşı korumak.</li>
          </ul>
        </Section>

        <Section title="4. Verilerin Aktarıldığı Üçüncü Taraflar">
          <p>
            Videonu klibe dönüştürebilmemiz için konuşma metnini çıkarma ve öne çıkan anları bulma
            işlemlerini bir yapay zeka sağlayıcısı (Anthropic Claude veya Google Gemini API&apos;si)
            üzerinden gerçekleştiriyoruz - bu işlem sırasında videonun ilgili içeriği bu sağlayıcıya
            iletilir. Doğrulama ve şifre sıfırlama e-postaların, tercih ettiğimiz e-posta gönderim
            altyapısı üzerinden gönderilir. Bu sağlayıcılar dışında verilerin hiçbir üçüncü tarafla
            pazarlama amacıyla paylaşılmadığını veya satılmadığını belirtiriz.
          </p>
        </Section>

        <Section title="5. Veri Saklama Süresi">
          <p>
            Verilerin, hesabın aktif olduğu sürece ve hizmeti sunabilmemiz için gerekli olduğu
            müddetçe saklanır. Hesabını sildiğinde e-posta adresin, video/klip dosyaların ve tüm iş
            kayıtların veritabanından ve sunucu depolamasından kalıcı olarak silinir - bu işlem geri
            alınamaz. Oturum jetonların en fazla 30 gün geçerlidir, bu sürenin sonunda otomatik olarak
            geçersiz hale gelir.
          </p>
        </Section>

        <Section title="6. KVKK Kapsamındaki Haklarınız">
          <p>KVKK&apos;nın 11. maddesi uyarınca şu haklara sahipsin:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Kişisel verinin işlenip işlenmediğini öğrenme,</li>
            <li>İşlenmişse buna ilişkin bilgi talep etme,</li>
            <li>İşlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme,</li>
            <li>Yurt içinde/dışında aktarıldığı üçüncü kişileri bilme,</li>
            <li>Eksik/yanlış işlenmişse düzeltilmesini isteme,</li>
            <li>Kanuna uygun olarak işlenmiş olsa bile, işlenmesini gerektiren sebeplerin ortadan kalkması hâlinde silinmesini veya yok edilmesini isteme,</li>
            <li>İşlenen verilerin münhasıran otomatik sistemler vasıtasıyla analiz edilmesi suretiyle aleyhine bir sonucun ortaya çıkmasına itiraz etme,</li>
            <li>Kanuna aykırı işlenmesi sebebiyle zarara uğraman hâlinde zararın giderilmesini talep etme.</li>
          </ul>
          <p>
            Bu haklarını kullanmak için{" "}
            <a href="mailto:brightnotedestek@gmail.com" className="text-orange-400 hover:underline">
              brightnotedestek@gmail.com
            </a>{" "}
            adresine yazabilir, veya doğrudan{" "}
            <Link href="/profil" className="text-orange-400 hover:underline">
              profilinden
            </Link>{" "}
            hesabını dilediğin zaman silebilirsin.
          </p>
        </Section>

        <Section title="7. Veri Güvenliği">
          <p>
            Şifreler tek yönlü (geri döndürülemez) bcrypt algoritmasıyla saklanır - hiçbir çalışanımız
            veya sistemimiz şifrenin kendisini göremez. Oturum erişimi süreli jetonlarla sağlanır ve
            şifre sıfırlandığında güvenlik amacıyla önceki tüm oturumlar otomatik olarak sonlandırılır.
          </p>
        </Section>

        <Section title="8. Çerezler (Cookies)">
          <p>
            Klipster şu an tarayıcı çerezi (cookie) kullanmamaktadır; oturum bilgisi tarayıcının yerel
            depolamasında (localStorage) tutulur ve yalnızca sana ait cihazda kalır.
          </p>
        </Section>

        <Section title="9. Değişiklikler">
          <p>
            Bu metni zaman zaman güncelleyebiliriz. Önemli değişikliklerde sayfanın en üstündeki
            &quot;son güncelleme&quot; tarihi değiştirilecek ve gerekirse hesabın üzerinden ayrıca
            bilgilendirileceksin.
          </p>
        </Section>
      </div>
    </main>
  );
}
