from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import posts, agents, graph

app = FastAPI(title="emotion-agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

images_dir = Path(__file__).parent.parent / "data" / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/data/images", StaticFiles(directory=str(images_dir)), name="images")

app.include_router(posts.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
