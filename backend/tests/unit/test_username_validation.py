import pytest

from validations.auth_validation import RegisterRequest

def test_valid_username_is_returned_lowercase():
    assert RegisterRequest.validate_username("Rai_01") == "rai_01"

def test_username_is_trimmed():
    assert RegisterRequest.validate_username("  Rai  ") == "rai"

@pytest.mark.parametrize(
    "username, esperado",
    [
        ("raikoch", "raikoch"),
        ("rai.koch", "rai.koch"),
        ("rai_koch", "rai_koch"),
        ("rai2301", "rai2301"),
        ("RAI", "rai"),
        ("r" * 30, "r" * 30),
        ("  Rai.Koch_01  ", "rai.koch_01"),
    ],
)
def test_valid_usernames_are_accepted(username, esperado):
    assert RegisterRequest.validate_username(username) == esperado

@pytest.mark.parametrize(
    "username, expected_message",
    [
        ("ra", "entre 3 y 30 caracteres"),
        ("r" * 31, "entre 3 y 30 caracteres"),
        ("", "entre 3 y 30 caracteres"),
        ("   ", "entre 3 y 30 caracteres"),
        ("rai koch", "letras, numeros, punto"),
        ("rai-koch", "letras, numeros, punto"),
        ("rai@ubiobio", "letras, numeros, punto"),
        ("rai#1", "letras, numeros, punto"),
        ("rai/koch", "letras, numeros, punto"),
        ("raiñ", "letras, numeros, punto"),
        ("rai\nkoch", "letras, numeros, punto"),
    ],
)
def test_invalid_username_raises_value_error(username, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        RegisterRequest.validate_username(username)

def test_the_error_message_explains_the_rule():
    with pytest.raises(ValueError) as excepcion:
        RegisterRequest.validate_username("rai koch")

    mensaje = str(excepcion.value)
    assert "letras, numeros, punto" in mensaje
    assert "guion bajo" in mensaje
    assert "entre 3 y 30 caracteres" in mensaje

def test_the_same_rule_applies_when_editing_the_profile():
    from validations.user_validation import UpdateProfileRequest

    assert UpdateProfileRequest.validate_username("Rai_01") == "rai_01"

    with pytest.raises(ValueError, match="letras, numeros, punto"):
        UpdateProfileRequest.validate_username("rai koch")

def test_editing_the_profile_allows_not_sending_the_username():
    from validations.user_validation import UpdateProfileRequest

    assert UpdateProfileRequest.validate_username(None) is None
