from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database.session import Base

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    origem_cep = Column(String(8), nullable=False)
    destino_cep = Column(String(8), nullable=False)
    distancia_km = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
