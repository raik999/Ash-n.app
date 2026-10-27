from datetime import date, timedelta

import pytest

from validations.user_validation import UpdateProfileRequest

HOY = date.today()

def fecha_de_alguien_de(anios: int) -> date:
    return date(HOY.year - anios, 1, 1)

@pytest.mark.parametrize("anios", [13, 14, 20, 45, 99, 120])
def test_a_valid_birthdate_is_returned_unchanged(anios):
    fecha = fecha_de_alguien_de(anios)
    assert UpdateProfileRequest.validate_birthdate(fecha) == fecha

def test_birthdate_none_is_accepted():
    assert UpdateProfileRequest.validate_birthdate(None) is None

def test_someone_born_exactly_13_years_ago_today_is_accepted():
    try:
        fecha = HOY.replace(year=HOY.year - 13)
    except ValueError:
        pytest.skip("hoy es 29 de febrero y hace 13 anios ese dia no existio")

    assert UpdateProfileRequest.validate_birthdate(fecha) == fecha

@pytest.mark.parametrize(
    "fecha, expected_message",
    [
        (HOY + timedelta(days=1), "no puede estar en el futuro"),
        (HOY + timedelta(days=365), "no puede estar en el futuro"),
        (date(HOY.year + 10, 6, 15), "no puede estar en el futuro"),
    ],
)
def test_a_birthdate_in_the_future_raises_value_error(fecha, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        UpdateProfileRequest.validate_birthdate(fecha)

def test_today_is_rejected_for_being_too_young():
    with pytest.raises(ValueError, match="al menos 13"):
        UpdateProfileRequest.validate_birthdate(HOY)

@pytest.mark.parametrize("anios", [0, 5, 12])
def test_a_child_under_13_raises_value_error(anios):
    with pytest.raises(ValueError, match="al menos 13"):
        UpdateProfileRequest.validate_birthdate(fecha_de_alguien_de(anios))

@pytest.mark.parametrize("anios", [121, 130, 200])
def test_an_impossible_age_raises_value_error(anios):
    with pytest.raises(ValueError, match="no parece valida"):
        UpdateProfileRequest.validate_birthdate(fecha_de_alguien_de(anios))

def test_each_rule_has_its_own_message():
    mensajes = []

    for fecha in [
        HOY + timedelta(days=1),
        fecha_de_alguien_de(12),
        fecha_de_alguien_de(130),
    ]:
        with pytest.raises(ValueError) as excepcion:
            UpdateProfileRequest.validate_birthdate(fecha)
        mensajes.append(str(excepcion.value))

    assert len(set(mensajes)) == 3
