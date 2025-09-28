from pydantic import BaseModel, Field, AliasChoices, constr
from typing import Optional

CepStr = constr(pattern=r"^\d{5}-?\d{3}$")

class Coordinates(BaseModel):
    longitude: Optional[float] = None
    latitude: Optional[float] = None

class GeoPoint(BaseModel):
    type: Optional[str] = None
    coordinates: Optional[Coordinates] = None

class CepPath(BaseModel):
    cep: CepStr

class CepOut(BaseModel):
    cep: str

    # Aceita ViaCEP (pt) e BrasilAPI (en):
    logradouro: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("logradouro", "street")
    )
    bairro: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("bairro", "neighborhood")
    )
    localidade: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("localidade", "city")
    )
    uf: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("uf", "state")
    )

    service: Optional[str] = None
    location: Optional[GeoPoint] = None

    # Ignora chaves extras como "ddd", etc., caso apareçam
    model_config = {"extra": "ignore"}
