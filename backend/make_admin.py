import sys

from config.database import SessionLocal
from entities.user import UserRole
from services.user_service import get_user_by_identifier


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python make_admin.py <nombre_de_usuario_o_mail> [--quitar]")
        return 1

    identifier = sys.argv[1]
    remove = "--quitar" in sys.argv
    new_role = UserRole.USER if remove else UserRole.ADMIN

    db = SessionLocal()
    try:
        user = get_user_by_identifier(db, identifier)

        if user is None:
            print(f"No se encontro ningun usuario con '{identifier}'")
            return 1

        if user.role == new_role:
            print(f"@{user.username} ya tiene el rol {new_role.value}")
            return 0

        user.role = new_role
        db.commit()

        print(f"Listo: @{user.username} ahora es {new_role.value}")
        print("Recuerda que tendra que volver a iniciar sesion para que su")
        print("token refleje el rol nuevo.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
