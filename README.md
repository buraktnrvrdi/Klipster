# İçerik Yeniden Üretim Aracı (Content Repurposer)

Uzun bir videoyu (podcast, röportaj, konuşma) yükle; yapay zeka en ilgi çekici
anları bulup senin için altyazılı, dikey (9:16) kısa klipler üretsin.

## Nasıl çalışıyor
1. Video yüklenir.
2. `faster-whisper` ile ses metne çevrilir (kelime bazlı zaman damgalarıyla).
3. Transkript Claude'a gönderilir, en ilgi çekici 3-6 klip anı (başlangıç/bitiş,
   başlık, neden ilgi çekici olduğu) tespit edilir.
4. `ffmpeg` ile her an videodan kesilir, 9:16 dikey formata kırpılır ve
   otomatik altyazı yakılır.

## Klasörler
- `backend/` — FastAPI + video işleme (Python)
- `frontend/` — Yükleme arayüzü (Next.js)

## Çalıştırmak için

### 1. Backend
```
cd backend
pip3 install -r requirements.txt
cp .env.example .env   # sonra .env içine ANTHROPIC_API_KEY'ini yaz
python3 -m uvicorn app.main:app --reload --port 8000
```
> Not: pip paketleri PATH dışına kurulduysa `uvicorn` komutu yerine
> `python3 -m uvicorn ...` kullan.

### 2. Frontend
```
cd frontend
npm run dev
```
Sonra tarayıcıda http://localhost:3000 adresini aç.

## Yapılacaklar / sonraki adımlar
- [ ] Anthropic API key alıp `backend/.env` içine eklemek
- [ ] Uzun videolarda ffmpeg render süresini iyileştirmek
- [ ] Kelime kelime vurgulanan (karaoke tarzı) altyazı efekti eklemek
- [ ] Klipleri doğrudan TikTok/Instagram'a paylaşma entegrasyonu
- [ ] Kullanıcı hesabı + abonelik/ödeme sistemi (Stripe/Iyzico)
