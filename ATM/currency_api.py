# currency_api.py
import requests
import time

# ---- DEFAULT API KEY (as you asked) ----
API_KEY = "cur_live_7ZXYGDFi0keAkRm5uRfL4ZJWHxm6gvQrhI8iaW3D"

# ---- API URL (from your dashboard) ----
BASE_URL = "https://api.currencyapi.com/v3/latest"

# ---- Cache (optional) ----
CACHE_TTL = 300  # 5 minutes
_cache = {"rates": None, "fetched_at": 0}


def _fetch_rates():
    """
    Fetch latest currency rates using your default key.
    """
    url = f"{BASE_URL}?apikey={API_KEY}&base_currency=INR"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json().get("data")

        if not data:
            return None

        # Convert API format to simple dict: {"USD": 0.0123, "EUR": 0.0111}
        rates = {code: float(info["value"]) for code, info in data.items()}
        return rates

    except Exception:
        return None


def get_rates():
    now = time.time()
    if _cache["rates"] and (now - _cache["fetched_at"] < CACHE_TTL):
        return _cache["rates"]

    rates = _fetch_rates()
    if rates:
        _cache["rates"] = rates
        _cache["fetched_at"] = now
        return rates

    # fallback default values (in case no internet)
    return {"USD": 0.012, "EUR": 0.011, "GBP": 0.0095}


def convert_inr(amount, currencies=("USD", "EUR", "GBP")):
    """
    Converts INR -> USD/EUR/GBP using live API or fallback.
    """
    rates = get_rates()
    result = {}

    for c in currencies:
        if c in rates:
            result[c] = amount * rates[c]

    return result
