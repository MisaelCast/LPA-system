from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.areas import router as areas_router
from app.api.auth import router as auth_router
from app.api.capas import router as capas_router
from app.api.celulas import router as celulas_router
from app.api.roles import router as roles_router
from app.api.usuarios import router as usuarios_router
from app.config import settings
from app.db.database import create_db_and_tables
from app.seed import seed_inicial


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()
    seed_inicial()
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

print("RAW CORS:", repr(settings.backend_cors_origins))
print("PARSED CORS:", settings.cors_origins_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(roles_router)
app.include_router(areas_router)
app.include_router(celulas_router)
app.include_router(capas_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "LPA System API"}
