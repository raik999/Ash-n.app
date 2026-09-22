import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.database import SessionLocal, init_database
from config.settings import settings
from middleware.error_middleware import register_error_handlers
from routes import auth_routes, tag_routes, user_routes
from seeds.seed_tags import seed_tags

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ashun")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Ashun API...")

    init_database()
    logger.info("Tablas verificadas")

    db = SessionLocal()
    try:
        created = seed_tags(db)
        if created:
            logger.info("Se crearon %d especialidades iniciales", created)
    finally:
        db.close()

    logger.info("API lista en http://localhost:%d", settings.port)
    logger.info("Documentacion interactiva en http://localhost:%d/docs", settings.port)

    yield

    logger.info("Apagando Ashun API...")


app = FastAPI(
    title="Ashun API",
    description="API de la red social para artistas Ashun",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_dir)),
    name="uploads",
)

register_error_handlers(app)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(tag_routes.router)


@app.get("/", tags=["Sistema"], summary="Saludo de la API")
def root() -> dict:
    return {
        "app": "Ashun API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Sistema"], summary="Estado de la API y la base de datos")
def health() -> dict:
    from sqlalchemy import text

    from config.database import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception as error:
        database_status = f"error: {error}"

    return {"status": "ok", "database": database_status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "index:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
