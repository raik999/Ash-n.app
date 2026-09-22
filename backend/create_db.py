import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from config.settings import settings


def main() -> int:
    print(f"Servidor:      {settings.db_host}:{settings.db_port}")
    print(f"Usuario:       {settings.db_username}")
    print(f"Base de datos: {settings.database}")
    print()

    engine = create_engine(settings.admin_url, isolation_level="AUTOCOMMIT")

    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.database},
            ).scalar_one_or_none()

            if exists:
                print(f"La base de datos '{settings.database}' ya existe.")
                return 0

            if not settings.database.replace("_", "").isalnum():
                print(f"Nombre de base de datos invalido: '{settings.database}'")
                print("Usa solo letras, numeros y guiones bajos.")
                return 1

            connection.execute(text(f'CREATE DATABASE "{settings.database}"'))
            print(f"Base de datos '{settings.database}' creada correctamente.")
            print()
            print("Siguiente paso:  python index.py")
            return 0

    except OperationalError as error:
        print("No se pudo conectar a PostgreSQL.")
        print()
        print("Revisa que:")
        print("  1. El servicio de PostgreSQL este corriendo en tu computador")
        print(f"  2. Este escuchando en {settings.db_host}:{settings.db_port}")
        print("  3. DB_USERNAME y DB_PASSWORD del archivo .env sean correctos")
        print()
        print(f"Detalle tecnico: {error.orig}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
