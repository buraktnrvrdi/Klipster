# Railway (ve benzeri konteyner tabanli platformlar) icin backend imaji.
# faster-whisper (transkript) ve video kirpma islemleri sistem seviyesinde
# ffmpeg'e ihtiyac duyuyor - bu yuzden saf bir Python imaji yerine ffmpeg'i
# de kuran bu Dockerfile kullaniliyor.

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# storage/ klasoru - kalici olmasi icin Railway'de bir Volume'un TAM OLARAK
# bu yola (/app/storage) baglanmasi gerekiyor, yoksa her yeni deploy'da
# yuklenen videolar ve veritabani silinir. Detaylar icin DEPLOY.md'ye bak.
RUN mkdir -p /app/storage

# Railway PORT ortam degiskenini kendisi atar - sabit bir port yerine onu
# kullanmamiz gerekiyor. Yerel test icin varsayilan olarak 8000 birakildi.
ENV PORT=8000
EXPOSE 8000

CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
