"""Gemini baglantisini izole test etmek icin."""
import os
from dotenv import load_dotenv
load_dotenv()

print("GEMINI_API_KEY set mi:", bool(os.environ.get("GEMINI_API_KEY")))

from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

print("İstek gönderiliyor...")
try:
    interaction = client.interactions.create(
        model="gemini-3.7-flash",
        system_instruction="Sen yardımcı bir asistansın.",
        input="Merhaba, sadece 'test basarili' yaz.",
    )
    print("CEVAP:", interaction.output_text)
except Exception as e:
    print("HATA TIPI:", type(e).__name__)
    print("HATA:", e)
