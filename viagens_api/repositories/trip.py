from sqlalchemy.orm import Session
from typing import Iterable, Optional
from models.trip import Trip

def create(db: Session, nome: str, origem_cep: str, destino_cep: str) -> Trip:
    t = Trip(nome=nome, origem_cep=origem_cep, destino_cep=destino_cep)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def list_all(db: Session) -> Iterable[Trip]:
    return db.query(Trip).all()

def get(db: Session, trip_id: int) -> Optional[Trip]:
    return db.get(Trip, trip_id)

def update(db: Session, t: Trip, *, nome=None, origem_cep=None, destino_cep=None) -> Trip:
    if nome is not None: t.nome = nome
    if origem_cep is not None: t.origem_cep = origem_cep
    if destino_cep is not None: t.destino_cep = destino_cep
    db.commit()
    db.refresh(t)
    return t

def delete(db: Session, t: Trip) -> None:
    db.delete(t)
    db.commit()
