"""Tek seferlik kurulum scripti: iyzico'da Klipster'in abonelik urunlerini
(Yaratici, Ajans) ve aylik fiyatlandirma planlarini olusturur, sonunda
.env / Railway'e eklenecek IYZICO_YARATICI_PLAN_CODE ve
IYZICO_AJANS_PLAN_CODE degerlerini yazdirir.

Kullanim (backend/ klasorunden):
    IYZICO_API_KEY=... IYZICO_SECRET_KEY=... IYZICO_BASE_URL=sandbox-api.iyzipay.com \
        python3 scripts/setup_iyzico_products.py

Not: Bu script sadece BIR KERE calistirilmali (sandbox icin bir kere, canliya
gecerken canli anahtarlarla bir kere daha). Tekrar calistirilirsa iyzico'da
ayni isimde ikinci bir urun/plan daha olusur - onceki kodlar gecerliligini
korur, sadece gereksiz tekrar olur.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import iyzipay

OPTIONS = {
    "api_key": os.environ["IYZICO_API_KEY"],
    "secret_key": os.environ["IYZICO_SECRET_KEY"],
    "base_url": os.environ.get("IYZICO_BASE_URL", "sandbox-api.iyzipay.com"),
}

PLANS = [
    {"key": "yaratici", "product_name": "Klipster Yaratıcı", "plan_name": "Yaratıcı Aylık", "price": 589},
    {"key": "ajans", "product_name": "Klipster Ajans", "plan_name": "Ajans Aylık", "price": 1490},
]


def _call(resource, method_name, body):
    method = getattr(resource, method_name)
    response = method(body, OPTIONS)
    data = json.loads(response.read().decode("utf-8"))
    if data.get("status") != "success":
        raise SystemExit(f"HATA ({resource.__class__.__name__}.{method_name}): {data}")
    print(f"  (ham yanıt: {json.dumps(data, ensure_ascii=False)[:400]})")
    # iyzico'nun v2 uc noktalari kaynagi bazen ust seviyede, bazen "data" altinda
    # dondurur - ikisini de dene (sandbox hesabi olmadan kesin sema dogrulanamadi).
    result = data.get("data") or data
    if "referenceCode" not in result:
        raise SystemExit(
            f"referenceCode alani yanitta bulunamadi, yukaridaki ham yaniti kontrol et: {result}"
        )
    return result


def main():
    print(f"Base URL: {OPTIONS['base_url']}\n")
    codes = {}
    for plan in PLANS:
        conv_id = uuid.uuid4().hex[:12]
        product = _call(
            iyzipay.SubscriptionProduct(),
            "create",
            {
                "locale": "tr",
                "conversationId": conv_id,
                "name": plan["product_name"],
                "description": f"{plan['product_name']} aylık abonelik",
            },
        )
        product_code = product["referenceCode"]
        print(f"[{plan['key']}] Ürün oluşturuldu: {product_code}")

        pricing_plan = _call(
            iyzipay.SubscriptionPricingPlan(),
            "create",
            {
                "locale": "tr",
                "conversationId": conv_id,
                "name": plan["plan_name"],
                "price": plan["price"],
                "currencyCode": "TRY",
                "paymentInterval": "MONTHLY",
                "paymentIntervalCount": 1,
                "planPaymentType": "RECURRING",
                "trialPeriodDays": 0,
                "product_reference_code": product_code,
            },
        )
        plan_code = pricing_plan["referenceCode"]
        print(f"[{plan['key']}] Fiyatlandırma planı oluşturuldu: {plan_code}\n")
        codes[plan["key"]] = plan_code

    print("Aşağıdaki satırları Railway ortam değişkenlerine (backend servisi) ekle:\n")
    print(f"IYZICO_YARATICI_PLAN_CODE={codes['yaratici']}")
    print(f"IYZICO_AJANS_PLAN_CODE={codes['ajans']}")


if __name__ == "__main__":
    main()
