import os, requests
DIST_API = os.getenv("DISTANCIA_API_URL", "http://localhost:8001")

def calcular_distancia_por_ceps(origem_cep: str, destino_cep: str) -> float:
    r = requests.post(f"{DIST_API}/distance/by-cep", json={"origem": origem_cep, "destino": destino_cep}, timeout=10)
    r.raise_for_status()
    return r.json()["distancia_km"]
