import requests
import os

BRASILAPI_URL = os.getenv("BRASILAPI_URL","https://brasilapi.com.br/api")
BASE = f"{BRASILAPI_URL}/cep/v2"

def get_latlon_by_cep(cep: str) -> dict:
    cep = ''.join(filter(str.isdigit, cep))[:8]
    r = requests.get(f"{BASE}/{cep}", timeout=10)
    r.raise_for_status()
    data = r.json()
    coords = data.get("location", {}).get("coordinates", {})
    return {
        "cep": data.get("cep"),
        "lat": float(coords.get("latitude")),
        "lon": float(coords.get("longitude")),
        "city": data.get("city"),
        "state": data.get("state"),
        "street": data.get("street"),
        "neighborhood": data.get("neighborhood"),
    }
