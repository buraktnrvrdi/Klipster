"""iyzico Abonelik (Subscription) API entegrasyonu.

iyzico'nun hazir "Checkout Form" widget'ini kullaniyoruz - kart bilgileri
hicbir zaman bizim sunucumuza gelmiyor, dogrudan iyzico'nun guvenli
sayfasina/iframe'ine giriliyor. Bu sayede PCI-DSS kapsamini (kart verisi
saklama/isleme sorumlulugu) tamamen iyzico'ya birakiyoruz.

Alan adlari (request body sozlukleri) iyzico'nun resmi Python SDK'sinin
(iyzipay-python) samples/subscriptions/ altindaki ornek dosyalarindan
birebir alinmistir - tahmin edilmemistir. Sadece basarili bir odeme
sonrasi donen yanitin ("callback") tam sekli sandbox hesabi olmadan
dogrulanamadi; bu yuzden retrieve_checkout_form() birden fazla olasi
alan adini deniyor ve ham yaniti veritabanina kaydediyor - ilk gercek
denemeden sonra gerekirse tek satirlik bir duzeltmeyle kesinlestirilir.
"""
import json
import logging
import os

import iyzipay

logger = logging.getLogger(__name__)

IYZICO_API_KEY = os.environ.get("IYZICO_API_KEY", "")
IYZICO_SECRET_KEY = os.environ.get("IYZICO_SECRET_KEY", "")
# Sandbox: sandbox-api.iyzipay.com , Canli: api.iyzipay.com
IYZICO_BASE_URL = os.environ.get("IYZICO_BASE_URL", "sandbox-api.iyzipay.com")

# iyzico panelinde/API'de bir kere olusturulup (bkz. backend/scripts/
# setup_iyzico_products.py) buraya .env'den yapistirilan fiyatlandirma
# plani referans kodlari.
PRICING_PLAN_CODES = {
    "yaratici": os.environ.get("IYZICO_YARATICI_PLAN_CODE", ""),
    "ajans": os.environ.get("IYZICO_AJANS_PLAN_CODE", ""),
}

PLAN_PRICES_TL = {"yaratici": 589, "ajans": 1490}
PLAN_LABELS = {"yaratici": "Yaratıcı", "ajans": "Ajans"}


class PaymentError(Exception):
    """Kullaniciya gosterilebilecek, Turkce bir mesaj tasiyan odeme hatasi."""


def is_configured() -> bool:
    return bool(IYZICO_API_KEY and IYZICO_SECRET_KEY)


def plan_is_purchasable(plan: str) -> bool:
    return bool(PRICING_PLAN_CODES.get(plan))


def _options() -> dict:
    return {
        "api_key": IYZICO_API_KEY,
        "secret_key": IYZICO_SECRET_KEY,
        "base_url": IYZICO_BASE_URL,
    }


def _request(resource, method_name: str, body: dict) -> dict:
    """iyzipay SDK'sindaki bir kaynagin (Subscription, SubscriptionCheckoutForm, ...)
    bir metodunu cagirir, ham HTTP yanitini JSON'a cevirir ve basarisizsa
    PaymentError firlatir."""
    method = getattr(resource, method_name)
    try:
        response = method(body, _options())
    except Exception as exc:
        logger.exception(
            "[iyzico] %s.%s cagrisi basarisiz", resource.__class__.__name__, method_name
        )
        raise PaymentError("Ödeme sağlayıcısına ulaşılamadı, lütfen daha sonra tekrar dene") from exc

    raw = response.read().decode("utf-8")
    try:
        data = json.loads(raw)
    except ValueError as exc:
        logger.error("[iyzico] %s.%s gecersiz JSON yaniti: %s", resource.__class__.__name__, method_name, raw[:1000])
        raise PaymentError("Ödeme sağlayıcısından geçersiz yanıt alındı") from exc

    data["_raw"] = raw
    if data.get("status") != "success":
        logger.warning(
            "[iyzico] %s.%s basarisiz (http=%s): %s",
            resource.__class__.__name__, method_name, getattr(response, "status", "?"), raw[:1000],
        )
        raise PaymentError(data.get("errorMessage") or "Ödeme işlemi başarısız oldu")
    return data


def create_checkout_form(*, plan: str, conversation_id: str, callback_url: str, buyer: dict) -> dict:
    """Kullaniciyi kart bilgisi girecegi iyzico checkout form'una yonlendirmek
    icin gereken 'token' ve 'checkoutFormContent' (frontend'e gomulecek
    JS/iframe kodu) degerlerini dondurur."""
    pricing_plan_code = PRICING_PLAN_CODES.get(plan)
    if not pricing_plan_code:
        raise PaymentError("Bu plan için ödeme yapılandırması eksik")

    full_name = f"{buyer['name']} {buyer['surname']}".strip()
    address = {
        "address": buyer["address"],
        "zipCode": buyer.get("zip_code") or "00000",
        "contactName": full_name,
        "city": buyer["city"],
        "country": "Türkiye",
    }
    request = {
        "callbackUrl": callback_url,
        "pricingPlanReferenceCode": pricing_plan_code,
        "subscriptionInitialStatus": "ACTIVE",
        "conversationId": conversation_id,
        "customer": {
            "name": buyer["name"],
            "surname": buyer["surname"],
            "email": buyer["email"],
            "gsmNumber": buyer["phone"],
            "identityNumber": buyer["identity_number"],
            "billingAddress": address,
            "shippingAddress": address,
        },
    }
    return _request(iyzipay.SubscriptionCheckoutForm(), "create", request)


def retrieve_checkout_form(token: str) -> dict:
    return _request(iyzipay.SubscriptionCheckoutForm(), "retrieve", {"token": token})


def cancel_subscription(subscription_reference_code: str) -> dict:
    return _request(
        iyzipay.Subscription(), "cancel", {"subscriptionReferenceCode": subscription_reference_code}
    )


def extract_subscription_status(data: dict) -> tuple[str | None, str | None, str | None]:
    """Checkout form retrieve yanitindan (subscriptionStatus, subscriptionReferenceCode,
    customerReferenceCode) cikarmaya calisir - iyzico'nun v2 abonelik API'si icin
    olasi birkac alan adi denenir, cunku bu yanitin tam semasi sandbox hesabi
    olmadan resmi ornek kodlardan dogrulanamadi."""
    status = (
        data.get("subscriptionStatus")
        or data.get("status_detail")
        or (data.get("data") or {}).get("subscriptionStatus")
    )
    reference_code = (
        data.get("subscriptionReferenceCode")
        or data.get("referenceCode")
        or (data.get("data") or {}).get("subscriptionReferenceCode")
        or (data.get("data") or {}).get("referenceCode")
    )
    customer_code = (
        data.get("customerReferenceCode")
        or (data.get("data") or {}).get("customerReferenceCode")
    )
    return status, reference_code, customer_code
