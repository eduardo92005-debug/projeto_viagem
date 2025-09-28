# Viagens API (principal) + Distância API (serviço)

Projeto composto por **duas APIs independentes**:

- **viagens-api (principal)** — CRUD de viagens em **SQLite** e orquestra o cálculo de distância chamando a `distancia-api`.
- **distancia-api (secundária)** — serviço que calcula **distância em linha reta** pelo método **Haversine** usando **latitude/longitude**; quando recebe CEPs BR, usa a **BrasilAPI CEP v2** para obter as coordenadas.

> **Observação:** a distância calculada é **em linha reta** (modelo **esférico** via Haversine). **Não representa rota por estrada**.

---

## Sumário

- [Arquitetura](#arquitetura)
- [Estrutura dos repositórios](#estrutura-dos-repositórios)
- [Tecnologias](#tecnologias)
- [Como executar (Docker Compose)](#como-executar-docker-compose)
- [Como executar localmente (sem Docker)](#como-executar-localmente-sem-docker)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Endpoints](#endpoints)
  - [distancia-api](#distancia-api)
  - [viagens-api](#viagens-api)
- [Fluxo principal](#fluxo-principal)
- [Logs (logger.py)](#logs-loggerpy)
- [Schemas & Repositories](#schemas--repositories)
- [Limitações e melhorias futuras](#limitações-e-melhorias-futuras)
- [Roteiro de apresentação (5–6 min)](#roteiro-de-apresentação-56-min)
- [Solução de problemas (FAQ)](#solução-de-problemas-faq)
- [Licença](#licença)

---

## Arquitetura

```
[Cliente/Swagger] → [viagens-api]
        |               |
        | (HTTP REST)   └──────→ [distancia-api] ──→ (HTTP) BrasilAPI CEP v2
        |                                      |
        └─ CRUD viagens (SQLite)  ←────────────┘  retorna distância em km
```

- **Comunicação:** HTTP/REST.
- **Persistência:** `viagens-api` usa **SQLite**.
- **API externa:** **BrasilAPI CEP v2** para converter CEP → latitude/longitude.
- **Cálculo:** **Haversine** (R=6371.0088 km, modelo esférico).

---

## Estrutura dos repositórios

Projetos **separados** (cada um em repositório público próprio). O **docker-compose** fica **na raiz da API principal**.

```
/projetos/
  viagens-api/            ← este repositório (principal) — contém o docker-compose.yml
    app.py
    logger.py
    database/
    models/
    repositories/
    routes/
    schemas/
    services/
    requirements.txt
    Dockerfile
    docker-compose.yml
    README.md

  distancia-api/          ← repositório secundário (serviço)
    app.py
    logger.py
    schemas/
    services/
    requirements.txt
    Dockerfile
    README.md
```

---

## Tecnologias

- **Python 3.12**
- **Flask** + **flask-openapi3** (Swagger/OpenAPI automático)
- **SQLAlchemy** (SQLite)
- **Requests** (HTTP externo)
- **Pydantic** (schemas de entrada/saída)
- **Docker** e **Docker Compose**
- **logger.py** (dictConfig): console + arquivos rotativos em `log/`

---

## Como executar (Docker Compose)

> Execute os comandos dentro da **pasta `viagens-api`**. O compose sobe **viagens-api** e **distancia-api** na mesma rede.

```bash
docker compose up -d --build
docker ps
```

Serviços:
- `viagens-api`: http://localhost:8000 (Swagger em **/openapi**)
- `distancia-api`: http://localhost:8001 (Swagger em **/openapi**)

Encerrar:
```bash
docker compose down
```

---

## Como executar localmente (sem Docker)

**distancia-api**:
```bash
cd distancia-api
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py  # porta 8001
```

**viagens-api** (em outro terminal):
```bash
cd viagens-api
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DISTANCIA_API_URL=http://localhost:8001  # Windows PowerShell: $Env:DISTANCIA_API_URL="http://localhost:8001"
python app.py  # porta 8000
```

---

## Variáveis de ambiente

`viagens-api`:
- `DATABASE_URL` (opcional): padrão `sqlite:///./viagens.db` (compose usa volume em `/app/data/viagens.db`).
- `DISTANCIA_API_URL`: URL da `distancia-api` (no Compose: `http://distancia-api:8001`).

`distancia-api`:
- sem obrigatórias (usa BrasilAPI pública).

---

## Endpoints

### distancia-api

- **GET /** → health básico.
- **POST /distance/by-coords**  
  **Body:**
  ```json
  {
    "origem":  { "lat": -23.5505, "lon": -46.6333 },
    "destino": { "lat": -22.9068, "lon": -43.1729 }
  }
  ```
  **Resposta:**
  ```json
  { "distancia_km": 357.123 }
  ```

- **POST /distance/by-cep**  
  **Body:**
  ```json
  { "origem": "01001000", "destino": "20040002" }
  ```
  **Resposta:**
  ```json
  {
    "distancia_km": 357.123,
    "origem":  { "cep":"01001000", "lat": -23.5505, "lon": -46.6333, "city":"São Paulo", "state":"SP", ... },
    "destino": { "cep":"20040002", "lat": -22.9068, "lon": -43.1729, "city":"Rio de Janeiro", "state":"RJ", ... }
  }
  ```

> Observação: distância **em linha reta** via Haversine (modelo esférico).

### viagens-api

- **GET /** → health básico.
- **GET /ceps/{cep}** → passthrough da BrasilAPI (opcional).
- **POST /trips** → cria viagem  
  **Body:**
  ```json
  { "nome": "Viagem SP-RJ", "origem_cep": "01001000", "destino_cep": "20040002" }
  ```
  **Resposta:**
  ```json
  { "id": 1, "nome":"Viagem SP-RJ", "origem_cep":"01001000", "destino_cep":"20040002", "distancia_km": null }
  ```

- **GET /trips** → lista viagens
- **GET /trips/{id}** → detalhe
- **PUT /trips/{id}** → atualiza nome/ceps
- **DELETE /trips/{id}**
- **GET /trips/{id}/distance** → chama a `distancia-api` e grava `distancia_km`  
  **Resposta:**
  ```json
  { "trip_id": 1, "distancia_km": 357.123 }
  ```

Todos os endpoints possuem **Swagger/OpenAPI** via `flask-openapi3`:
- `viagens-api`: `http://localhost:8000/openapi`
- `distancia-api`: `http://localhost:8001/openapi`

---

## Fluxo principal

1. Criar viagem na **viagens-api** (`POST /trips`).
2. Pedir o cálculo (`GET /trips/{id}/distance`): a principal chama a **distancia-api**.
3. A **distancia-api** resolve `lat/lon` com **BrasilAPI CEP v2** (se por CEP) e aplica **Haversine**.
4. A **viagens-api** grava `distancia_km` no banco SQLite e retorna ao cliente.

---

## Logs (logger.py)

As duas APIs usam **o mesmo `logger.py`** (dictConfig) com:
- saída no **console**;
- arquivos rotativos em `log/gunicorn.detailed.log` e `log/gunicorn.error.log`;
- formato detalhado com timestamp, nível, função e linha.

Basta `from logger import logger` e usar `logger.info(...)`, `logger.error(..., exc_info=True)`, etc.

---

## Schemas & Repositories

- **Schemas (Pydantic)** em `schemas/` (ex.: `TripCreate`, `TripUpdate`, `TripOut`) — usados nas assinaturas das rotas para o **Swagger**.
- **Repositories** em `repositories/` isolam persistência (`trip_repository.py`: `create`, `list_all`, `get`, `update`, `delete`).
- **Services** em `services/` fazem chamadas HTTP externas (`brasilapi.py`, `distancia_client.py`).

Essa organização segue o estilo do repositório `api-flask-aula`: camadas bem definidas, rotas registradas por função (`register_*_routes`).

---

## Limitações e melhorias futuras

- **Distância Haversine**: é em **linha reta** numa **esfera** — ótima para estimativas gerais. Para rotas reais (estradas) seria necessário integrar **API de rotas** (OSRM, GraphHopper, Google Directions).
- **Paginação/filtragem** em `/trips`: pode ser adicionada (`?limit=&offset=&order=`).
- **Cache** de CEPs em memória ou Redis para reduzir chamadas externas.
- **Autenticação** e **rate limiting** se necessário para produção.

---

## Roteiro de apresentação (5–6 min)

1. **Introdução (30s):** objetivo do projeto, dois módulos, cálculo de distância em linha reta por CEP.
2. **Arquitetura (45s):** mostrar diagrama e explicar comunicação REST.
3. **API externa (45s):** BrasilAPI CEP v2 → exibir `services/brasilapi.py` e/ou `GET /ceps/{cep}`.
4. **distancia-api (1m15s):** abrir Swagger, testar `by-cep` e `by-coords` (mostrar `distancia_km`).
5. **viagens-api (1m15s):** abrir Swagger, `POST /trips`, `GET /trips/{id}/distance`, `GET /trips`.
6. **Encerramento (15s):** reforçar separação de módulos, Swagger, SQLite, logs e consumo de API externa.
