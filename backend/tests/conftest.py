import os
import tempfile
import pytest

os.environ["DATABASE"] = "ashun_test"

os.environ["DATABASE_URL"] = ""

os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="ashun_pruebas_")

@pytest.fixture(scope="session")
def base_de_pruebas():
    
    from sqlalchemy import create_engine, text
    from config.database import init_database
    from config.settings import settings

    admin = create_engine(settings.admin_url, isolation_level="AUTOCOMMIT")

    with admin.connect() as conexion:
        existe = conexion.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
            {"nombre": settings.database},
        ).scalar()

        if not existe:
            conexion.execute(text(f'CREATE DATABASE "{settings.database}"'))

    admin.dispose()

    init_database()

    yield
