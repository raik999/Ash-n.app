import pytest

from pydantic import ValidationError
from validations.auth_validation import RegisterRequest

def registro_con(email: str) -> RegisterRequest:
    return RegisterRequest(
        email=email,
        name="Raimundo Koch",
        username="raikoch",
        password="Secreta123",
        confirm_password="Secreta123",
    )

@pytest.mark.parametrize(
    "email",
    [
        "raimundo.koch2301@alumnos.ubiobio.cl",
        "rai@ubiobio.cl",
        "rai_koch@gmail.com",
        "rai+pruebas@gmail.com",
        "r@x.cl",
    ],
)
def test_valid_email_is_accepted(email):
    assert registro_con(email).email == email

@pytest.mark.parametrize(
    "email, por_que",
    [
        ("", "vacio"),
        ("rai", "no tiene arroba"),
        ("rai ubiobio.cl", "un espacio en vez de la arroba"),
        ("@ubiobio.cl", "no hay nada antes de la arroba"),
        ("rai@", "no hay nada despues de la arroba"),
        ("rai@@ubiobio.cl", "dos arrobas"),
        ("rai@ubiobio", "el dominio no tiene punto"),
        ("rai@.cl", "el dominio empieza con punto"),
        ("rai koch@ubiobio.cl", "un espacio en el medio"),
    ],
)
def test_invalid_email_is_rejected(email, por_que):
    with pytest.raises(ValidationError):
        registro_con(email)

def test_the_error_points_at_the_email_field():
    with pytest.raises(ValidationError) as excepcion:
        registro_con("no-es-un-correo")

    errores = excepcion.value.errors()
    assert len(errores) == 1
    assert errores[0]["loc"] == ("email",)

def test_the_email_is_required():
    with pytest.raises(ValidationError) as excepcion:
        RegisterRequest(
            name="Raimundo Koch",
            username="raikoch",
            password="Secreta123",
            confirm_password="Secreta123",
        )

    assert excepcion.value.errors()[0]["type"] == "missing"
