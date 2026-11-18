export type Block =
  | { type: "p"; text: string }
  | { type: "h2"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] };

export type Post = {
  slug: string;
  title: string;
  description: string;
  date: string;
  readMinutes: number;
  blocks: Block[];
};

export const POSTS: Post[] = [
  {
    slug: "uzun-videodan-tiktok-reels-shorts-klibi-nasil-cikarilir",
    title: "Uzun videodan TikTok, Reels ve Shorts klibi nasıl çıkarılır?",
    description:
      "Podcast, röportaj veya canlı yayın kaydından kısa dikey klipler çıkarmanın adımları: doğru anı bulmak, kırpmak, altyazı eklemek ve paylaşmak.",
    date: "2026-11-18",
    readMinutes: 6,
    blocks: [
      {
        type: "p",
        text: "Saatlik bir podcast, uzun bir röportaj ya da canlı yayın kaydı çoğu zaman içinde onlarca paylaşılabilir an barındırır. Sorun, bu anları bulup kısa ve dikey bir klibe dönüştürmenin saatler sürmesi. Bu rehberde, uzun bir videodan TikTok, Instagram Reels ve YouTube Shorts için klip çıkarmanın adımlarını ve nelere dikkat etmen gerektiğini anlatıyoruz.",
      },
      { type: "h2", text: "1. Önce doğru anı seç" },
      {
        type: "p",
        text: "İyi bir kısa klip, bağlamdan bağımsız olarak tek başına anlaşılan bir an olmalı. Konuşmanın içinde şunlara denk gelen kısımlar genelde işe yarar:",
      },
      {
        type: "ul",
        items: [
          "Beklenmedik bir itiraf, ilginç bir anekdot ya da net bir fikir",
          "Güçlü bir görüş bildirilen ya da tartışma yaratabilecek cümle",
          "Bir soruya doğrudan, kısa ve etkileyici cevap verilen kısım",
          "Duygusal bir tepkinin yaşandığı ya da komik bir anın geçtiği yer",
        ],
      },
      {
        type: "p",
        text: "Klip, ilk 2–3 saniyede izleyiciyi tutmalı. Konuşmanın ortasında başlayan ama kendini hemen açıklayan bir an, uzun bir girişle başlayan kısımdan çok daha iyi performans gösterir.",
      },
      { type: "h2", text: "2. Süreyi kısa tut" },
      {
        type: "p",
        text: "Kısa video platformlarında 20–60 saniye arası klipler genellikle en rahat izlenen aralıktır. Daha uzun bir an varsa, onu mantıklı bir yerden iki parçaya bölmek çoğu zaman daha iyi sonuç verir. Her klibin bir başı ve bir sonu olmalı; yarım kalmış cümleyle bitmemeli.",
      },
      { type: "h2", text: "3. Videoyu dikey formata çevir" },
      {
        type: "p",
        text: "TikTok, Reels ve Shorts dikey (9:16) izlenmek üzere tasarlandı. Yatay çekilmiş bir görüntüyü dikeye çevirirken konuşanın yüzü kadrajda kalmalı; sadece ortadan kesmek, kenara yakın duran kişiyi kadraj dışında bırakabilir. Instagram'da 4:5 ya da 1:1 oran da kullanılıyor, hangi platforma paylaşacağına göre en-boy oranını seçmek gerekir.",
      },
      { type: "h2", text: "4. Altyazı ekle" },
      {
        type: "p",
        text: "İzleyicilerin önemli bir kısmı videoyu sessiz izler. Altyazı hem erişilebilirliği hem de izlenme süresini artırır. Altyazı konuşmayla senkron olmalı, ekrana sığmayacak kadar uzun satırlardan kaçınılmalı ve yazı tipi arka plandan net ayrılmalı. Kelime kelime beliren altyazılar dikkati çekmek için sık kullanılan bir yöntem.",
      },
      { type: "h2", text: "5. Dolgu kelimeleri ve sessizlikleri temizle" },
      {
        type: "p",
        text: "\"Şey\", \"ıı\", \"eee\" gibi dolgu sesler ve uzun duraklamalar, kısa bir klipte tempoyu düşürür. Bunları kırpmak klibi daha akıcı yapar. Elle yapıldığında bu iş zaman alıcı; kare kare kırpmak yerine bunu otomatik yapan araçlar işi hızlandırır.",
      },
      { type: "h2", text: "6. Kapak görseli ve başlık" },
      {
        type: "p",
        text: "Paylaşımın kapağı, profil sayfasında ve keşfet akışında ilk gördükleri şey. Videodan net bir kare seçip kısa ve merak uyandıran bir başlık eklemek tıklanma oranını etkiler.",
      },
      { type: "h2", text: "Bunu elle mi yapmalı, otomatik mi?" },
      {
        type: "p",
        text: "Elle yapınca bir video editörü açıp videoyu baştan sona izlemen, anları not etmen, kırpman, dikeye çevirmen ve altyazıyı eklemen gerekir. Bir saatlik video için bu saatlerce sürebilir. Klipster bu adımların hepsini senin yerine yapar: videonu yüklersin (ya da YouTube linkini yapıştırırsın), yapay zeka konuşmayı dinleyip en çarpıcı anları bulur, dikey formata kırpar, altyazıyı ekler, dolgu kelimeleri temizler ve kapak görselini hazırlar. Sonuçları MP4 olarak indirir ya da doğrudan YouTube Shorts'a yükleyebilirsin.",
      },
      {
        type: "p",
        text: "Ücretsiz planda ayda 2 video işleyebilir ve her videodan 4 klip alabilirsin; kayıt olup denemek için kredi kartı gerekmiyor.",
      },
    ],
  },
  {
    slug: "videoya-otomatik-altyazi-nasil-eklenir",
    title: "Videoya otomatik altyazı nasıl eklenir? (Türkçe altyazı rehberi)",
    description:
      "Videoya Türkçe otomatik altyazı eklemenin yolları, altyazının izlenme süresine etkisi ve okunaklı altyazı için dikkat edilecek ayrıntılar.",
    date: "2026-11-18",
    readMinutes: 5,
    blocks: [
      {
        type: "p",
        text: "Kısa video platformlarında insanların büyük bir bölümü videoyu sessiz izliyor. Altyazı olmayan bir video, sesi açılmadığı sürece mesajını iletemiyor. Bu yüzden altyazı artık isteğe bağlı bir süs değil, neredeyse zorunlu bir unsur. Bu rehberde videoya Türkçe altyazı eklemenin yollarını ve iyi bir altyazının nasıl görünmesi gerektiğini anlatıyoruz.",
      },
      { type: "h2", text: "Altyazı eklemenin üç yolu" },
      {
        type: "ol",
        items: [
          "Elle yazmak: Video editöründe her cümleyi dinleyip yazar ve zamanlarsın. En kontrollü yöntem ama en yavaşı; bir dakikalık videoda bile uzun sürebilir.",
          "Platformun kendi otomatik altyazısı: Bazı platformlar otomatik altyazı sunar. Hızlıdır ama görünümü ve zamanlaması üzerinde çok az kontrolün olur, Türkçede hatalar sık görülebilir.",
          "Yapay zeka destekli araçlar: Konuşmayı yazıya çevirip kelime düzeyinde zamanlar ve videoya gömer. Hem hızlı hem de görünüm ayarlanabilir.",
        ],
      },
      { type: "h2", text: "İyi bir altyazıda neler olmalı?" },
      {
        type: "ul",
        items: [
          "Konuşmayla senkron: Yazı, söylendiği anda ekrana gelmeli. Geç ya da erken görünen altyazı dikkat dağıtır.",
          "Kısa satırlar: Ekrana sığmayan ya da çok uzun satırlar okunmaz. Bir seferde birkaç kelime göstermek en rahat okunan yöntem.",
          "Net kontrast: Yazı tipi arka plandan ayrışmalı; kontur veya gölge okunurluğu artırır.",
          "Doğru yazım: Özellikle özel isimler ve Türkçe karakterler (ç, ğ, ı, ö, ş, ü) doğru yazılmalı.",
          "Güvenli alan: Altyazı, platformun arayüz öğelerinin (butonlar, açıklama metni) altında kalmayacak bir yerde durmalı.",
        ],
      },
      { type: "h2", text: "Kelime kelime altyazı neden popüler?" },
      {
        type: "p",
        text: "Konuşulan kelimenin belirdiği an vurgulandığı altyazı stilleri, izleyicinin gözünü ekranda tutar ve konuşmanın ritmini takip etmeyi kolaylaştırır. Bu stillerde kelime düzeyinde zamanlama gerektiği için, elle yapmak çok zahmetli; bu iş için otomatik araçlar tercih edilir.",
      },
      { type: "h2", text: "Klipster ile otomatik Türkçe altyazı" },
      {
        type: "p",
        text: "Klipster, videodaki konuşmayı kelime düzeyinde zaman damgalarıyla yazıya çevirir ve dili otomatik algılar. Altyazıyı konuşmayla senkron olarak klibin üzerine işler; farklı stil ve animasyon seçenekleri arasından görünümü seçebilirsin. İhtiyaç olursa altyazıyı başka dillere çevirip ayrı dosya olarak da indirebilirsin.",
      },
      {
        type: "p",
        text: "Dolgu kelimeler (\"şey\", \"ıı\", \"eee\") ve uzun sessizlikler de otomatik kırpıldığı için hem altyazı hem klip daha akıcı çıkar.",
      },
    ],
  },
  {
    slug: "youtube-videosunu-shortsa-cevirme",
    title: "YouTube videosunu YouTube Shorts'a nasıl çevirirsin?",
    description:
      "Uzun bir YouTube videosundan Shorts klipleri çıkarmak için adımlar: doğru anı seçmek, dikey formata çevirmek, altyazı eklemek ve yüklemek.",
    date: "2026-11-18",
    readMinutes: 5,
    blocks: [
      {
        type: "p",
        text: "YouTube'da yayınladığın uzun videolar, Shorts için hazır bir içerik madeni. Aynı videonun en ilgi çekici anlarını dikey kliplere çevirmek, yeni içerik çekmeden kanalına yeni izleyiciler getirmenin en pratik yollarından biri. Bu rehberde uzun bir YouTube videosunu Shorts klibine çevirmenin adımlarını anlatıyoruz.",
      },
      { type: "h2", text: "YouTube Shorts için temel kurallar" },
      {
        type: "ul",
        items: [
          "Dikey (9:16) format kullan.",
          "Süreyi kısa tut; Shorts için sınır platform tarafından belirlenir ve zaman içinde değişebilir, güncel süre sınırını YouTube'un yardım sayfasından kontrol et.",
          "İlk saniyelerde dikkat çek; izleyici hemen kaydırabilir.",
          "Sessiz izleyenler için altyazı ekle.",
        ],
      },
      { type: "h2", text: "Adım adım: uzun videodan Shorts'a" },
      {
        type: "ol",
        items: [
          "Videoyu izle ya da transkriptini çıkar ve öne çıkan anları işaretle: güçlü bir cümle, komik bir an, net bir tavsiye.",
          "Her anı kendi başına anlaşılacak şekilde kırp; önceki bağlama ihtiyaç duyan kısımlardan kaçın.",
          "Yatay görüntüyü dikeye çevir ve konuşanın yüzünü kadrajda tut.",
          "Altyazı ekle; konuşmayla senkron ve okunaklı olsun.",
          "Başlık ve açıklama yaz; arama ve keşfet için anahtar kelimeleri kullan.",
          "Shorts olarak yükle ve performansı takip ederek hangi tür anların daha iyi çalıştığını gör.",
        ],
      },
      { type: "h2", text: "Elle yapmak yerine otomatikleştir" },
      {
        type: "p",
        text: "Bir saatlik videoyu baştan sona izleyip kırpmak, dikeye çevirmek ve altyazı eklemek saatler alır. Klipster'da YouTube linkini yapıştırman yeterli: video indirilir, konuşma yazıya çevrilir, yapay zeka en çarpıcı anları bulur, dikey formata kırpar ve altyazıyı ekler. Hazır klipleri MP4 olarak indirebilir ya da YouTube kanalını bağlayıp klip düzenleme ekranından doğrudan Shorts olarak yükleyebilirsin.",
      },
      {
        type: "p",
        text: "Dikkat: Yalnızca kendi içeriğin olan ya da yeniden kullanma hakkına sahip olduğun videolardan klip çıkar. Başkasının videosunu izinsiz yeniden yüklemek telif hakkı sorunlarına yol açabilir.",
      },
    ],
  },
];

export function getPost(slug: string): Post | undefined {
  return POSTS.find((p) => p.slug === slug);
}
