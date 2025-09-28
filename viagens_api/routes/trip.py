# routes/trip.py
from flask_openapi3 import Tag
from flask import g
from logger import logger
from repositories import trip as repo
from schemas.trip import TripCreate, TripUpdate, TripOut, TripsOut, TripPath
from services.distancia_client import calcular_distancia_por_ceps
from services.brasilapi import get_cep, CepNotFound, MissingCoordinates, BrasilAPIError

trip_tag = Tag(name="Trips", description="Operações de viagens")

def register_trip_routes(app):
    @app.post("/trips", tags=[trip_tag], responses={"201": TripOut, "400": {"description": "bad cep"}})
    def create_trip(body: TripCreate):
        origem = body.origem_cep.replace("-", "").strip()
        destino = body.destino_cep.replace("-", "").strip()
        logger.info(f"[create_trip] recebido nome={body.nome} origem_cep={origem} destino_cep={destino}")

        try:
            logger.debug(f"[create_trip] validando origem_cep={origem} na BrasilAPI")
            get_cep(origem, require_coords=True)
            logger.info(f"[create_trip] origem_cep válido e com coordenadas: {origem}")
        except CepNotFound:
            logger.warning(f"[create_trip] origem_cep inválido: {origem}")
            return {"error": "invalid_cep", "field": "origem_cep", "cep": origem}, 400
        except MissingCoordinates:
            logger.warning(f"[create_trip] origem_cep sem coordenadas: {origem}")
            return {"error": "missing_coordinates", "field": "origem_cep", "cep": origem}, 400
        except BrasilAPIError as e:
            logger.error(f"[create_trip] falha ao consultar BrasilAPI para origem_cep={origem}: {e}")
            return {"error": "cep_lookup_failed", "field": "origem_cep"}, 400

        try:
            logger.debug(f"[create_trip] validando destino_cep={destino} na BrasilAPI")
            get_cep(destino, require_coords=True)
            logger.info(f"[create_trip] destino_cep válido e com coordenadas: {destino}")
        except CepNotFound:
            logger.warning(f"[create_trip] destino_cep inválido: {destino}")
            return {"error": "invalid_cep", "field": "destino_cep", "cep": destino}, 400
        except MissingCoordinates:
            logger.warning(f"[create_trip] destino_cep sem coordenadas: {destino}")
            return {"error": "missing_coordinates", "field": "destino_cep", "cep": destino}, 400
        except BrasilAPIError as e:
            logger.error(f"[create_trip] falha ao consultar BrasilAPI para destino_cep={destino}: {e}")
            return {"error": "cep_lookup_failed", "field": "destino_cep"}, 400

        t = repo.create(g.db, body.nome, origem, destino)
        logger.info(f"[create_trip] trip criada com sucesso id={t.id} origem_cep={origem} destino_cep={destino}")

        resp = TripOut(
            id=t.id, nome=t.nome,
            origem_cep=t.origem_cep, destino_cep=t.destino_cep,
            distancia_km=t.distancia_km
        )
        return resp.model_dump(), 201

    @app.get("/trips", tags=[trip_tag], responses={"200": TripsOut})
    def list_trips():
        logger.debug("[list_trips] iniciando listagem")
        qs = repo.list_all(g.db)
        items = [
            TripOut(
                id=x.id, nome=x.nome,
                origem_cep=x.origem_cep, destino_cep=x.destino_cep,
                distancia_km=x.distancia_km
            )
            for x in qs
        ]
        logger.info(f"[list_trips] total={len(items)}")
        return TripsOut(items=items).model_dump(), 200

    @app.get("/trips/<int:trip_id>", tags=[trip_tag],
             responses={"200": TripOut, "404": {"description": "not found"}})
    def get_trip(path: TripPath):
        logger.debug(f"[get_trip] buscando trip_id={path.trip_id}")
        t = repo.get(g.db, path.trip_id)
        if not t:
            logger.warning(f"[get_trip] trip não encontrada trip_id={path.trip_id}")
            return {"error": "not found"}, 404
        resp = TripOut(
            id=t.id, nome=t.nome,
            origem_cep=t.origem_cep, destino_cep=t.destino_cep,
            distancia_km=t.distancia_km
        )
        logger.info(f"[get_trip] sucesso trip_id={t.id}")
        return resp.model_dump(), 200

    @app.put("/trips/<int:trip_id>", tags=[trip_tag],
             responses={"200": {"description": "ok"}, "404": {"description": "not found"}})
    def update_trip(path: TripPath, body: TripUpdate):
        logger.debug(f"[update_trip] iniciando trip_id={path.trip_id}")
        t = repo.get(g.db, path.trip_id)
        if not t:
            logger.warning(f"[update_trip] trip não encontrada trip_id={path.trip_id}")
            return {"error": "not found"}, 404
        repo.update(
            g.db, t,
            nome=body.nome, origem_cep=body.origem_cep, destino_cep=body.destino_cep
        )
        logger.info(f"[update_trip] concluído trip_id={t.id}")
        return {"ok": True}, 200

    @app.delete("/trips/<int:trip_id>", tags=[trip_tag],
                responses={"200": {"description": "ok"}, "404": {"description": "not found"}})
    def delete_trip(path: TripPath):
        logger.debug(f"[delete_trip] iniciando trip_id={path.trip_id}")
        t = repo.get(g.db, path.trip_id)
        if not t:
            logger.warning(f"[delete_trip] trip não encontrada trip_id={path.trip_id}")
            return {"error": "not found"}, 404
        repo.delete(g.db, t)
        logger.info(f"[delete_trip] concluído trip_id={path.trip_id}")
        return {"ok": True}, 200

    @app.get("/trips/<int:trip_id>/distance", tags=[trip_tag],
             responses={"200": {"description": "ok"}, "404": {"description": "not found"}})
    def compute_distance(path: TripPath):
        logger.debug(f"[compute_distance] iniciando trip_id={path.trip_id}")
        t = repo.get(g.db, path.trip_id)
        if not t:
            logger.warning(f"[compute_distance] trip não encontrada trip_id={path.trip_id}")
            return {"error": "not found"}, 404
        dist = calcular_distancia_por_ceps(t.origem_cep, t.destino_cep)
        t.distancia_km = dist
        g.db.commit()
        logger.info(f"[compute_distance] atualizado trip_id={t.id} distancia_km={dist}")
        return {"trip_id": t.id, "distancia_km": dist}, 200
