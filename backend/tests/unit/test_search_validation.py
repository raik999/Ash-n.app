import pytest
from pydantic import ValidationError
from validations.search_validation import AddSearchRequest

@pytest.mark.parametrize(
    "escrito, esperado",
    [
        ("acuarela", "acuarela"),
        ("  acuarela  ", "acuarela"),
        ("\tacuarela\n", "acuarela"),
        ("oleo sobre tela", "oleo sobre tela"),
        ("Acuarela", "Acuarela"),
    ],
)
def test_the_search_text_is_trimmed(escrito, esperado):
    assert AddSearchRequest.clean_value(escrito) == esperado

@pytest.mark.parametrize("vacio", ["", "   ", "\t", "\n", "  \t \n "])
def test_a_blank_search_is_rejected(vacio):
    with pytest.raises(ValueError, match="no puede estar vacia"):
        AddSearchRequest.clean_value(vacio)

@pytest.mark.parametrize("tipo", ["query", "user"])
def test_the_two_valid_kinds_are_accepted(tipo):
    peticion = AddSearchRequest(kind=tipo, value="acuarela")

    assert peticion.kind == tipo
    assert peticion.value == "acuarela"

@pytest.mark.parametrize(
    "tipo, por_que",
    [
        ("tag", "un tipo que no existe"),
        ("Query", "el tipo correcto pero con mayuscula"),
        ("", "vacio"),
        ("post", "parece razonable, pero no esta permitido"),
    ],
)
def test_any_other_kind_is_rejected(tipo, por_que):
    with pytest.raises(ValidationError):
        AddSearchRequest(kind=tipo, value="acuarela")

def test_the_kind_is_required():
    with pytest.raises(ValidationError) as excepcion:
        AddSearchRequest(value="acuarela")

    assert excepcion.value.errors()[0]["type"] == "missing"

def test_a_search_of_exactly_60_characters_is_accepted():
    justo = "a" * 60

    peticion = AddSearchRequest(kind="query", value=justo)

    assert peticion.value == justo
    assert len(peticion.value) == 60

def test_a_search_longer_than_60_characters_is_rejected():
    with pytest.raises(ValidationError):
        AddSearchRequest(kind="query", value="a" * 61)

def test_the_length_is_measured_before_trimming():
    con_espacios = "a" * 58 + "   "

    assert len(con_espacios) == 61
    assert len(con_espacios.strip()) == 58

    with pytest.raises(ValidationError):
        AddSearchRequest(kind="query", value=con_espacios)

def test_a_complete_valid_request():
    peticion = AddSearchRequest(kind="user", value="  anapintora  ")

    assert peticion.kind == "user"
    assert peticion.value == "anapintora"
