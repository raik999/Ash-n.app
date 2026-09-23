from __future__ import annotations

import secrets

from pathlib import Path
from config.settings import settings
from middleware.error_middleware import ValidationError

ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

MAGIC_NUMBERS: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
]


def _detect_image_type(content: bytes) -> str | None:
    for signature, mime in MAGIC_NUMBERS:
        if content.startswith(signature):
            return mime

    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"

    return None


def save_avatar(user_id: int, filename: str, content_type: str, content: bytes) -> str:
    if len(content) == 0:
        raise ValidationError("El archivo esta vacio", field="file")

    if len(content) > settings.max_upload_size:
        max_mb = settings.max_upload_size // (1024 * 1024)
        raise ValidationError(f"La imagen no puede pesar mas de {max_mb} MB", field="file")

    detected = _detect_image_type(content)
    if detected is None:
        raise ValidationError(
            "El archivo no es una imagen valida (solo JPG, PNG, WEBP o GIF)",
            field="file",
        )

    if detected not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f"Tipo de imagen no permitido: {detected}", field="file")

    extension = ALLOWED_IMAGE_TYPES[detected]

    random_part = secrets.token_hex(8)
    safe_filename = f"{user_id}_{random_part}{extension}"

    destination: Path = settings.upload_dir / safe_filename

    for old_file in settings.upload_dir.glob(f"{user_id}_*"):
        if old_file.is_file():
            old_file.unlink(missing_ok=True)

    with open(destination, "wb") as file_handle:
        file_handle.write(content)

    return f"/uploads/{safe_filename}"


def delete_avatar(avatar_url: str) -> None:
    if not avatar_url:
        return

    filename = Path(avatar_url).name
    file_path = settings.upload_dir / filename

    if file_path.is_file():
        file_path.unlink(missing_ok=True)
