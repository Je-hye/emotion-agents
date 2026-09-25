import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import posts, agents, graph, ws as ws_routes

app = FastAPI(title="emotion-agents API")

_cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_data_dir = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent.parent / "data")))
images_dir = _data_dir / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/data/images", StaticFiles(directory=str(images_dir)), name="images")

app.include_router(posts.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(ws_routes.router)

_web_dist = Path(__file__).parent.parent / "web" / "dist"
if _web_dist.exists():
    app.mount("/", StaticFiles(directory=str(_web_dist), html=True), name="spa")
