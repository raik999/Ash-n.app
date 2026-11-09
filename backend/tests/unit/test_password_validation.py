import pytest
from pydantic import ValidationError

from services.security_service import hash_password, verify_password
from validations.auth_validation import RegisterRequest
from validations.user_validation import ChangePasswordRequest

def test_hash_password_does_not_return_the_plain_password():
    assert hash_password("Secreta123") != "Secreta123"

def test_hash_password_returns_a_bcrypt_hash():
    resultado = hash_password("Secreta123")

    assert resultado.startswith("$2b$")
    assert len(resultado) == 60

def test_the_same_password_produces_two_different_hashes():
    assert hash_password("Secreta123") != hash_password("Secreta123")

def test_verify_password_accepts_the_correct_password():
    guardado = hash_password("Secreta123")

    assert verify_password("Secreta123", guardado) is True

@pytest.mark.parametrize(
    "intento, por_que",
    [
        ("secreta123", "cambia una mayuscula"),
        ("SECRETA123", "todo en mayusculas"),
        ("Secreta124", "un digito distinto"),
        ("Secreta12", "le falta el ultimo caracter"),
        ("Secreta123 ", "un espacio de mas al final"),
        (" Secreta123", "un espacio de mas al principio"),
        ("", "vacia"),
    ],
)
def test_verify_password_rejects_a_wrong_password(intento, por_que):
    guardado = hash_password("Secreta123")

    assert verify_password(intento, guardado) is False, f"deberia fallar: {por_que}"

def test_verify_password_returns_false_with_a_broken_hash():
    assert verify_password("Secreta123", "esto-no-es-un-hash") is False
    assert verify_password("Secreta123", "") is False

def test_a_password_of_exactly_72_bytes_is_accepted():
    clave = "a" * 72

    assert RegisterRequest.validate_password(clave) == clave

def test_a_password_longer_than_72_bytes_raises_value_error():
    with pytest.raises(ValueError, match="demasiado larga"):
        RegisterRequest.validate_password("a" * 73)

def test_the_limit_counts_bytes_and_not_characters():
    assert len("ñ" * 36) == 36
    assert len(("ñ" * 36).encode("utf-8")) == 72

    assert RegisterRequest.validate_password("ñ" * 36) == "ñ" * 36

    with pytest.raises(ValueError, match="demasiado larga"):
        RegisterRequest.validate_password("ñ" * 37)

def registro_con(password: str, confirm: str) -> RegisterRequest:
    return RegisterRequest(
        email="rai@ubiobio.cl",
        name="Raimundo Koch",
        username="raikoch",
        password=password,
        confirm_password=confirm,
    )

def test_matching_passwords_are_accepted():
    registro = registro_con("Secreta123", "Secreta123")

    assert registro.password == "Secreta123"

def test_passwords_that_do_not_match_are_rejected():
    with pytest.raises(ValidationError, match="no coinciden"):
        registro_con("Secreta123", "Secreta124")

def test_the_comparison_is_exact():
    with pytest.raises(ValidationError, match="no coinciden"):
        registro_con("Secreta123", "secreta123")

    with pytest.raises(ValidationError, match="no coinciden"):
        registro_con("Secreta123", "Secreta123 ")

@pytest.mark.parametrize("corta", ["", "a", "12345"])
def test_a_password_shorter_than_6_characters_is_rejected(corta):
    with pytest.raises(ValidationError):
        registro_con(corta, corta)

def cambio(actual: str, nueva: str, confirmar: str) -> ChangePasswordRequest:
    return ChangePasswordRequest(
        current_password=actual,
        new_password=nueva,
        confirm_password=confirmar,
    )

def test_a_valid_password_change_is_accepted():
    peticion = cambio("Secreta123", "Nueva456789", "Nueva456789")

    assert peticion.new_password == "Nueva456789"

def test_the_two_new_passwords_must_match():
    with pytest.raises(ValidationError, match="no coinciden"):
        cambio("Secreta123", "Nueva456789", "Nueva456780")

def test_the_new_password_must_be_different_from_the_current_one():
    with pytest.raises(ValidationError, match="distinta a la actual"):
        cambio("Secreta123", "Secreta123", "Secreta123")

def test_the_new_password_also_respects_the_72_byte_limit():
    larga = "a" * 73
    with pytest.raises(ValidationError, match="at most 72 characters"):
        cambio("Secreta123", larga, larga)

    con_enies = "ñ" * 37
    assert len(con_enies) == 37
    assert len(con_enies.encode("utf-8")) == 74

    with pytest.raises(ValidationError, match="demasiado larga"):
        cambio("Secreta123", con_enies, con_enies)

def test_36_enies_are_accepted_as_a_new_password():
    justa = "ñ" * 36

    peticion = cambio("Secreta123", justa, justa)

    assert peticion.new_password == justa

def test_the_full_round_trip_of_a_password():
    escrita_al_registrarse = "Secreta123"

    guardado_en_la_base = hash_password(escrita_al_registrarse)

    assert verify_password("Secreta123", guardado_en_la_base) is True
    assert verify_password("otra-cosa", guardado_en_la_base) is False
