from pydantic import BaseModel, Field, constr
from typing import Optional, List

CEP = constr(pattern=r"^\d{8}$")

class TripCreate(BaseModel):
    nome: constr(min_length=1, max_length=120)
    origem_cep: CEP = Field(..., description="CEP somente números (8 dígitos)")
    destino_cep: CEP = Field(..., description="CEP somente números (8 dígitos)")

class TripUpdate(BaseModel):
    nome: Optional[constr(min_length=1, max_length=120)] = None
    origem_cep: Optional[CEP] = None
    destino_cep: Optional[CEP] = None

class TripOut(BaseModel):
    id: int
    nome: str
    origem_cep: str
    destino_cep: str
    distancia_km: Optional[float] = None
    
class TripsOut(BaseModel):
    items: List[TripOut]

class TripPath(BaseModel):
    trip_id: int