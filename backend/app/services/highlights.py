"""Transkripti bir AI modeline gonderip en 'viral olabilecek' klip anlarini bulur,
ve (istege bagli) altyazi metinlerini Ingilizce'ye cevirir.

AI_PROVIDER ortam degiskeni ile saglayici secilir:
  - "gemini"    -> Google Gemini (ucretsiz katmani var, test icin uygun)
  - "anthropic" -> Claude (varsayilan, urun kalitesi icin onerilir)
"""
import json
import os

SYSTEM_PROMPT_TEMPLATE = """Sen bir sosyal medya icerik editorusun. Sana zaman damgali bir video \
transkripti verilecek. Gorevin, bu videodan TikTok/Instagram Reels/YouTube Shorts icin \
en ilgi cekici, bagimsiz anlasilabilir, {min_duration:.0f}-{max_duration:.0f} saniye arasi \
en fazla {max_clips} klip onerisi cikarmak.

Transkript HANGI DILDE ise (Turkce, Ingilizce, Almanca, fark etmez), baslik ve aciklamalari \
DA O DILDE yaz - transkriptin dilini degistirme veya Turkce'ye cevirme.

Her klip icin: net bir baslangic ve bitis noktasi (cumle/dusunce tam bitmis olmali), \
dikkat cekici bir kanca (hook) barindirmali, kisa bir baslik, neden ilgi cekici oldugunu \
aciklayan bir cumle, ve bu klibin sosyal medyada ne kadar 'viral' olabilecegini tahmin \
eden 0 ile 100 arasinda bir puan (score) uret. Puanlarken kancanin gucunu, duygusal \
yogunlugu, sasirticiligi ve bagimsiz anlasilirligini dikkate al.

SADECE asagidaki JSON formatinda cevap ver, baska hicbir metin ekleme:
{{
  "clips": [
    {{"start": 12.5, "end": 58.3, "title": "...", "reason": "...", "score": 78}}
  ]
}}
"""

TRANSLATE_SYSTEM_PROMPT = """Sen profesyonel bir altyazi cevirmenisin. Sana JSON formatinda \
bir metin dizisi (array) verilecek - kaynak dil ne olursa olsun (Turkce, Almanca, Fransizca, vb.) \
otomatik olarak tespit et. Her elemani, altyazi olarak kullanilacak sekilde kisa, akici ve \
dogal bir Ingilizceye cevir. Sira ve eleman sayisi degismemeli.

SADECE, verilenle AYNI UZUNLUKTA bir JSON dizisi dondur, baska hicbir metin ekleme. Ornek:
["Hello there", "This is amazing"]
"""

_anthropic_client = None
_gemini_client = None


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        headers = {}
        workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")
        if workspace_id:
            headers["anthropic-workspace-id"] = workspace_id
        _anthropic_client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            default_headers=headers or None,
        )
    return _anthropic_client


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return _gemini_client


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw


def _clean_json(raw: str) -> dict:
    return json.loads(_strip_code_fence(raw))


def _run_prompt(system_prompt: str, user_prompt: str) -> str:
    provider = os.environ.get("AI_PROVIDER", "anthropic").lower()
    if provider == "gemini":
        model = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
        interaction = _get_gemini_client().interactions.create(
            model=model,
            system_instruction=system_prompt,
            input=user_prompt,
        )
        return interaction.output_text
    message = _get_anthropic_client().messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def find_highlights(
    segments: list,
    max_clips: int = 5,
    min_duration: float = 20.0,
    max_duration: float = 75.0,
) -> list:
    transcript_text = "\n".join(
        f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments
    )
    user_prompt = f"En fazla {max_clips} klip oner. Transkript:\n\n{transcript_text}"
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        max_clips=max_clips, min_duration=min_duration, max_duration=max_duration,
    )
    raw = _run_prompt(system_prompt, user_prompt)
    data = _clean_json(raw)
    return data.get("clips", [])


def translate_to_english(lines: list[str]) -> list[str]:
    """Kisa altyazi metinlerinden olusan bir listeyi Ingilizce'ye cevirir.
    Girdiyle AYNI SAYIDA eleman donmezse hata firlatir (cagiran taraf best-effort
    olarak yakalayip yoksayabilir)."""
    if not lines:
        return []
    user_prompt = json.dumps(lines, ensure_ascii=False)
    raw = _run_prompt(TRANSLATE_SYSTEM_PROMPT, user_prompt)
    translated = json.loads(_strip_code_fence(raw))
    if not isinstance(translated, list) or len(translated) != len(lines):
        raise ValueError("Ceviri sonucu beklenmeyen formatta veya eksik/fazla eleman iceriyor")
    return [str(t) for t in translated]


TRANSLATE_GENERIC_SYSTEM_PROMPT_TEMPLATE = """Sen profesyonel bir altyazi cevirmenisin. Sana JSON formatinda \
bir metin dizisi (array) verilecek - kaynak dil ne olursa olsun otomatik olarak tespit et. Her elemani, \
altyazi olarak kullanilacak sekilde kisa, akici ve dogal bir {target_language} diline cevir. Sira ve \
eleman sayisi degismemeli.

SADECE, verilenle AYNI UZUNLUKTA bir JSON dizisi dondur, baska hicbir metin ekleme. Ornek:
["..."]
"""


def translate_subtitles(lines: list[str], target_language: str) -> list[str]:
    """translate_to_english'in genellenmis hali - kullanicinin sectigi HERHANGI
    bir hedef dile altyazi cevirisi yapar (bkz. app.main.SUBTITLE_LANGUAGES)."""
    if not lines:
        return []
    system_prompt = TRANSLATE_GENERIC_SYSTEM_PROMPT_TEMPLATE.format(target_language=target_language)
    user_prompt = json.dumps(lines, ensure_ascii=False)
    raw = _run_prompt(system_prompt, user_prompt)
    translated = json.loads(_strip_code_fence(raw))
    if not isinstance(translated, list) or len(translated) != len(lines):
        raise ValueError("Ceviri sonucu beklenmeyen formatta veya eksik/fazla eleman iceriyor")
    return [str(t) for t in translated]


SOCIAL_CAPTION_SYSTEM_PROMPT = """Sen bir sosyal medya icerik yoneticisisin. Sana bir video klibin \
transkript metni verilecek. Bu klip icin TikTok/Instagram Reels/YouTube Shorts'ta paylasilmaya hazir, \
dikkat cekici bir paylasim metni (caption) ve 5-8 adet ilgili hashtag uret.

Transkript HANGI DILDE ise caption ve hashtag'ler DE O DILDE olsun - dili degistirme veya Turkce'ye cevirme.

Caption kisa (1-3 cumle), merak uyandiran veya net bir deger onerisi sunan bir ton tasisin, uygun oldugunda \
emoji kullanabilir. Hashtag'ler # isareti OLMADAN, bosluksuz tek kelime/bitisik ifadeler olarak dondurulmeli.

SADECE asagidaki JSON formatinda cevap ver, baska hicbir metin ekleme:
{
  "caption": "...",
  "hashtags": ["hashtag1", "hashtag2", "..."]
}
"""


def generate_social_caption(transcript_text: str) -> dict:
    """Bir klibin transkript metninden sosyal medya paylasim metni (caption) ve
    hashtag onerileri uretir."""
    user_prompt = f"Klip transkripti:\n\n{transcript_text}"
    raw = _run_prompt(SOCIAL_CAPTION_SYSTEM_PROMPT, user_prompt)
    data = _clean_json(raw)
    caption = str(data.get("caption", "")).strip()
    hashtags = [str(h).strip().lstrip("#") for h in data.get("hashtags", []) if str(h).strip()]
    return {"caption": caption, "hashtags": hashtags}
