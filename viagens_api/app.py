from flask_openapi3 import OpenAPI, Info
from flask_cors import CORS
from flask import g
from database.session import Base, engine, SessionLocal
from routes.trip import register_trip_routes
from routes.cep import register_cep_routes

info = Info(title="Viagens API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

Base.metadata.create_all(bind=engine)

@app.before_request
def before_request():
    g.db = SessionLocal()

@app.teardown_request
def teardown_request(exc):
    db = g.pop('db', None)
    if db: db.close()

@app.get("/")
def root():
    return {"message": "Viagens API ok"}

register_trip_routes(app)
register_cep_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
