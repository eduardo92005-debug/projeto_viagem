from flask_openapi3 import Tag
from logger import logger
from services.brasilapi import get_cep
from schemas.cep import CepOut, CepPath

cep_tag = Tag(name="CEPs", description="Consulta CEP via BrasilAPI")

def register_cep_routes(app):
    @app.get("/ceps/<string:cep>", tags=[cep_tag],
             responses={"200": CepOut, "400": {"description": "bad cep"}})
    def consultar_cep(path: CepPath):
        cep = path.cep.replace("-", "")
        try:
            data = get_cep(cep)
            if not data:
                return {"error": "invalid_cep"}, 400
            logger.info(f"cep {cep} ok")
            return CepOut.model_validate(data).model_dump(), 200
        except Exception as e:
            logger.error(f"[consultar_cep] ocorreu algum erro: {e}")
            return {"error": "invalid_cep"}, 400
