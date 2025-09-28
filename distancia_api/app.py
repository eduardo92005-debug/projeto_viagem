from flask_openapi3 import OpenAPI, Info
from flask_cors import CORS
from flask import request, jsonify
from math import radians, sin, cos, asin, sqrt
from services.brasilapi import get_latlon_by_cep

info = Info(title="Distância API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0088
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*R*asin(sqrt(a))

@app.get("/")
def root():
    return {"message": "Distancia API ok"}

@app.post("/distance/by-coords")
def by_coords():
    b = request.get_json(force=True)
    dist = haversine(b["origem"]["lat"], b["origem"]["lon"], b["destino"]["lat"], b["destino"]["lon"])
    return jsonify({"distancia_km": round(dist, 3)}), 200

@app.post("/distance/by-cep")
def by_cep():
    b = request.get_json(force=True)
    o = get_latlon_by_cep(b["origem"])
    d = get_latlon_by_cep(b["destino"])
    dist = haversine(o["lat"], o["lon"], d["lat"], d["lon"])
    return jsonify({"distancia_km": round(dist, 3), "origem": o, "destino": d}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
