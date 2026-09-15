# Klipster - Canlıya Alma Rehberi (GitHub + Railway + Vercel)

Bu rehber, projeyi yerel bilgisayarından çıkarıp internete açman için gereken adımları anlatır. Hesap açma ve GitHub'a bağlama gibi adımlar senin kendi bilgilerini (e-posta, şifre) gerektirdiği için bu kısımları sen yapacaksın - ben sadece yönlendiriyorum.

Backend → **Railway**, frontend → **Vercel** üzerinde barınacak.

---

## 1. Adım: GitHub'a Push Et

Proje zaten yerelde git deposu olarak hazır (ilk commit atıldı). Şimdi bunu GitHub'a taşıman gerekiyor.

1. [github.com](https://github.com) üzerinden hesabın yoksa oluştur, varsa giriş yap.
2. Sağ üstteki **+** işaretine tıkla → **New repository**.
3. İsim ver (örneğin `klipster`), **Private** seçili kalsın (kaynak kodun herkese açık olmasın), **"Add a README"** kutucuğunu **işaretleme** (zaten var).
4. **Create repository** butonuna bas.
5. Açılan sayfada "…or push an existing repository from the command line" kısmındaki komutları göreceksin, onlara benzer şekilde kendi terminalinde (proje klasöründeyken) şunları çalıştır:

```bash
cd ~/Desktop/dekstop-claude\ proje
git remote add origin https://github.com/KULLANICI_ADIN/klipster.git
git branch -M main
git push -u origin main
```

GitHub kullanıcı adın ve şifren yerine artık bir "Personal Access Token" isteyecek - GitHub bunu ekranda anlatıyor, istenirse `github.com/settings/tokens` üzerinden bir token oluşturup şifre yerine onu yapıştırman yeterli.

---

## 2. Adım: Railway'de Backend'i Yayına Al

1. [railway.app](https://railway.app) adresine git, **"Login with GitHub"** ile giriş yap (GitHub hesabınla bağlanır).
2. **New Project** → **Deploy from GitHub repo** → az önce oluşturduğun `klipster` deposunu seç.
3. Railway repoyu tarayınca kök dizinde hem `backend/` hem `frontend/` gördüğü için hangisini deploy edeceğini sormayabilir - proje ayarlarından (**Settings → Root Directory**) bunu **`backend`** olarak ayarla. Bu önemli: Railway sadece backend klasörünü build almalı.
4. Railway `backend/Dockerfile`'ı otomatik bulup onunla build alacak (railway.toml zaten bunu tanımlıyor).

### Kalıcı Depolama (Volume) Ekle - ÇOK ÖNEMLİ

Bu adımı atlarsan her yeni deploy'da yüklenen videolar ve veritabanı (kullanıcılar, hesaplar) **silinir**.

1. Railway projende backend servisine tıkla → **Settings** sekmesi → **Volumes** bölümü.
2. **"+ New Volume"** butonuna bas.
3. **Mount Path** olarak tam olarak şunu yaz: `/app/storage`
4. Kaydet.

### Ortam Değişkenlerini (Environment Variables) Gir

Backend servisinde **Variables** sekmesine git ve `.env` dosyandaki değerlerin aynısını buraya tek tek ekle:

- `AI_PROVIDER` (anthropic veya gemini, hangisini kullanıyorsan)
- `ANTHROPIC_API_KEY` veya `GEMINI_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`
- `FRONTEND_URL` → Vercel'e deploy ettikten sonra alacağın adres (örn: `https://klipster.vercel.app`) - bu adımı 3. adımdan sonra geri gelip dolduracaksın
- `ALLOWED_ORIGINS` → gerekirse ekstra izinli adresler, virgülle ayrılmış

Değişkenleri kaydettikten sonra Railway otomatik olarak yeniden build alıp deploy edecek.

### Deploy'u Doğrula

Deploy bitince Railway sana bir genel adres verir (örn: `https://klipster-backend-production.up.railway.app`). Tarayıcıdan `.../healthz` ekleyerek ziyaret et (`https://klipster-backend-production.up.railway.app/healthz`) - `{"status":"ok"}` görürsen backend ayakta demektir.

Bu adresi bir yere not et, 3. adımda frontend'e bunu vereceğiz.

---

## 3. Adım: Vercel'de Frontend'i Yayına Al

1. [vercel.com](https://vercel.com) adresine git, **"Continue with GitHub"** ile giriş yap.
2. **Add New** → **Project** → `klipster` deposunu seç.
3. **Root Directory** ayarını **`frontend`** olarak değiştir (Vercel genelde otomatik algılar, algılamazsa elle seç).
4. **Environment Variables** kısmına şunu ekle:
   - `NEXT_PUBLIC_API_URL` → Railway'den aldığın backend adresi (örn: `https://klipster-backend-production.up.railway.app`, sonunda `/` olmadan)
5. **Deploy** butonuna bas.

Deploy tamamlanınca Vercel sana bir adres verir (örn: `https://klipster.vercel.app`, veya kendi seçtiğin bir isimle).

---

## 4. Adım: Geri Dönüp Railway'i Güncelle

Şimdi elinde gerçek Vercel adresin var. Railway'e geri dön → backend servisi → **Variables** → `FRONTEND_URL` değerini gerçek Vercel adresinle güncelle (örn: `https://klipster.vercel.app`). Kaydettiğinde Railway otomatik yeniden deploy alır.

Bu adım önemli çünkü e-posta doğrulama linkleri ve CORS izinleri bu adrese göre çalışıyor.

---

## 5. Adım: Test Et

1. Vercel adresine git, yeni bir hesap oluşturmayı dene.
2. Doğrulama e-postasının gelip gelmediğini kontrol et, linke tıkla.
3. Bir video yükleyip klip oluşturmayı dene.
4. Sunucu loglarını görmek istersen Railway projendeki **Deployments** sekmesinden canlı logları izleyebilirsin.

---

## Sonrasında: Kendi Alan Adını Bağlamak (opsiyonel)

Hem Railway hem Vercel, **Settings → Domains** üzerinden kendi domainini (örn. `klipster.com`) bağlamana izin veriyor. Bunu yaptığında `FRONTEND_URL` ve `NEXT_PUBLIC_API_URL` değerlerini yeni domain'lere göre tekrar güncellemeyi unutma.

## Notlar

- Ödeme sistemi (Stripe/iyzico) henüz eklenmedi - bu bilinçli olarak en sona bırakıldı, platform şu an sadece ücretsiz planla çalışıyor.
- `burak7k7@gmail.com` adresi şu an SMTP gönderim adresi olarak kullanılıyor - kalıcı bir adrese geçtiğinde Railway'deki `SMTP_USER`/`SMTP_PASS` değişkenlerini güncellemeyi unutma.
- Videolar büyüdükçe Railway Volume'un disk alanı sınırlı kalabilir; ileride Cloudflare R2 gibi bir S3-uyumlu depolamaya geçiş bir yükseltme seçeneği olarak değerlendirilebilir.
