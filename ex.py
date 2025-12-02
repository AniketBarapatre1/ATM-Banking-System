import requests

BASE = "USD"
TARGET = "INR"
url = f"https://api.exchangerate.host/latest"

params = {"base": BASE, "symbols": TARGET}

resp = requests.get(url, params=params, timeout=10)
resp.raise_for_status()
data = resp.json()

rate = data["rates"].get(TARGET)
print(f"1 {BASE} = {rate} {TARGET}")
