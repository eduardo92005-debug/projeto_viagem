# services/brasilapi.py
from __future__ import annotations
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import TypedDict, Optional
import os

BRASILAPI_URL = os.getenv("BRASILAPI_URL","https://brasilapi.com.br/api")
BASE = f"{BRASILAPI_URL}/cep/v2"

class Coordinates(TypedDict, total=False):
    latitude: Optional[float] | str
    longitude: Optional[float] | str

class Location(TypedDict, total=False):
    type: Optional[str]
    coordinates: Optional[Coordinates]

class CepPayload(TypedDict, total=False):
    cep: str
    state: Optional[str]
    city: Optional[str]
    neighborhood: Optional[str]
    street: Optional[str]
    service: Optional[str]
    location: Optional[Location]

class BrasilAPIError(Exception): ...
class CepNotFound(BrasilAPIError): ...
class MissingCoordinates(BrasilAPIError): ...

_session: requests.Session | None = None

def _get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        _session = s
    return _session

def _normalize_cep(cep: str) -> str:
    digits = "".join(ch for ch in cep if ch.isdigit())
    return digits[:8]

def _has_coords(data: CepPayload) -> bool:
    coords = (data.get("location") or {}).get("coordinates") or {}
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    return (lat not in (None, "",)) and (lon not in (None, "",))

def get_cep(cep: str, *, require_coords: bool = False) -> CepPayload:
    """
    Busca CEP na BrasilAPI.
    - Lança CepNotFound se o CEP não existir (404).
    - Lança MissingCoordinates se require_coords=True e não houver latitude/longitude.
    - Lança BrasilAPIError para outros erros (timeout, payload inválido, etc.).
    """
    cep = _normalize_cep(cep)
    if len(cep) != 8:
        raise CepNotFound(f"CEP inválido: {cep!r}")

    try:
        r = _get_session().get(f"{BASE}/{cep}", timeout=10)
    except requests.RequestException as e:
        raise BrasilAPIError(f"falha de rede ao consultar CEP {cep}: {e}") from e

    if r.status_code == 404:
        raise CepNotFound(f"CEP não encontrado: {cep}")

    if r.status_code >= 400:
        raise BrasilAPIError(f"erro HTTP {r.status_code} ao consultar CEP {cep}: {r.text[:200]}")

    try:
        data: CepPayload = r.json()
    except ValueError as e:
        raise BrasilAPIError(f"payload inválido (não é JSON) para CEP {cep}") from e

    if require_coords and not _has_coords(data):
        raise MissingCoordinates(f"CEP {cep} sem coordenadas")

    return data
