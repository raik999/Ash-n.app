import pytest

from config.settings import settings
from middleware.error_middleware import ValidationError
from services.storage_service import _detect_image_type, save_avatar

JPG = b"\xff\xd8\xff" + b"\x00" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
GIF87 = b"GIF87a" + b"\x00" * 100
GIF89 = b"GIF89a" + b"\x00" * 100

WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 100

@pytest.mark.parametrize(
    "contenido, esperado",
    [
        (JPG, "image/jpeg"),
        (PNG, "image/png"),
        (GIF87, "image/gif"),
        (GIF89, "image/gif"),
        (WEBP, "image/webp"),
    ],
)
def test_detect_image_type_recognises_the_four_allowed_formats(contenido, esperado):
    assert _detect_image_type(contenido) == esperado

@pytest.mark.parametrize(
    "contenido, que_es",
    [
        (b"", "un archivo vacio"),
        (b"Hola, soy un texto", "un .txt"),
        (b"%PDF-1.7\n", "un PDF"),
        (b"PK\x03\x04", "un ZIP o un .docx"),
        (b"MZ\x90\x00", "un .exe de Windows"),
        (b"\x7fELF", "un ejecutable de Linux"),
        (b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE", "un audio .wav disfrazado de RIFF"),
    ],
)
def test_detect_image_type_returns_none_for_anything_else(contenido, que_es):
    assert _detect_image_type(contenido) is None, f"debio rechazar {que_es}"

def test_an_empty_file_is_rejected():
    with pytest.raises(ValidationError, match="esta vacio"):
        save_avatar(user_id=1, filename="foto.jpg", content_type="image/jpeg", content=b"")

def test_an_image_over_5_mb_is_rejected():
    demasiado_grande = b"\xff\xd8\xff" + b"\x00" * settings.max_upload_size

    with pytest.raises(ValidationError, match="no puede pesar mas de"):
        save_avatar(1, "enorme.jpg", "image/jpeg", demasiado_grande)

def test_an_image_of_exactly_the_limit_is_not_rejected_for_size(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", tmp_path)

    justo_en_el_limite = b"\xff\xd8\xff" + b"\x00" * (settings.max_upload_size - 3)
    assert len(justo_en_el_limite) == settings.max_upload_size

    url = save_avatar(1, "limite.jpg", "image/jpeg", justo_en_el_limite)
    assert url.startswith("/uploads/")

@pytest.mark.parametrize(
    "contenido, que_es",
    [
        (b"Hola, soy un texto plano", "un .txt renombrado a .jpg"),
        (b"%PDF-1.7\n" + b"\x00" * 50, "un PDF"),
        (b"MZ\x90\x00" + b"\x00" * 50, "un .exe de Windows"),
        (b"PK\x03\x04" + b"\x00" * 50, "un .zip"),
        (b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"\x00" * 50, "un audio .wav"),
    ],
)
def test_a_file_that_is_not_an_image_is_rejected(contenido, que_es):
    with pytest.raises(ValidationError, match="no es una imagen valida"):
        save_avatar(1, "foto.jpg", "image/jpeg", contenido)

def test_the_error_names_the_allowed_formats():
    with pytest.raises(ValidationError) as excepcion:
        save_avatar(1, "foto.jpg", "image/jpeg", b"no soy una imagen")

    mensaje = str(excepcion.value)
    for formato in ["JPG", "PNG", "WEBP", "GIF"]:
        assert formato in mensaje

def test_the_error_points_at_the_file_field():
    with pytest.raises(ValidationError) as excepcion:
        save_avatar(1, "foto.jpg", "image/jpeg", b"")

    assert excepcion.value.field == "file"

@pytest.mark.parametrize(
    "contenido, extension",
    [
        (JPG, ".jpg"),
        (PNG, ".png"),
        (GIF89, ".gif"),
        (WEBP, ".webp"),
    ],
)
def test_a_valid_image_is_saved_with_the_right_extension(
    contenido, extension, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "upload_dir", tmp_path)

    url = save_avatar(7, "loquesea.txt", "application/octet-stream", contenido)

    assert url.endswith(extension)
    assert url.startswith("/uploads/7_")

    guardado = tmp_path / url.removeprefix("/uploads/")
    assert guardado.is_file()
    assert guardado.read_bytes() == contenido

def test_the_saved_name_is_not_the_one_the_user_chose(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", tmp_path)

    url = save_avatar(7, "../../index.py", "image/jpeg", JPG)

    assert ".." not in url
    assert "index" not in url
    assert url.startswith("/uploads/7_")

    archivos = list(tmp_path.iterdir())
    assert len(archivos) == 1

def test_uploading_a_new_avatar_deletes_the_old_one(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", tmp_path)

    primera = save_avatar(7, "a.jpg", "image/jpeg", JPG)
    segunda = save_avatar(7, "b.png", "image/png", PNG)

    assert primera != segunda
    assert len(list(tmp_path.iterdir())) == 1
    assert not (tmp_path / primera.removeprefix("/uploads/")).exists()

def test_changing_one_users_avatar_does_not_touch_another_users(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", tmp_path)

    otro = save_avatar(99, "otro.jpg", "image/jpeg", JPG)
    save_avatar(7, "mia.jpg", "image/jpeg", JPG)
    save_avatar(7, "mia2.png", "image/png", PNG)

    assert (tmp_path / otro.removeprefix("/uploads/")).is_file()
    assert len(list(tmp_path.iterdir())) == 2
