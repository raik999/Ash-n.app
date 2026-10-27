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

from entities.post_file import KIND_AUDIO, KIND_IMAGE, KIND_VIDEO

MEDIA_EXTENSIONS: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/x-msvideo": ".avi",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/mp4": ".m4a",
}

def _detect_media(content: bytes) -> tuple[str | None, str | None]:
    image_mime = _detect_image_type(content)
    if image_mime is not None:
        return image_mime, KIND_IMAGE

    if len(content) >= 12 and content[4:8] == b"ftyp":
        brand = content[8:12]
        if brand[:3] == b"M4A":
            return "audio/mp4", KIND_AUDIO
        return "video/mp4", KIND_VIDEO

    if content.startswith(b"RIFF") and len(content) >= 12:
        subtype = content[8:12]
        if subtype == b"WEBP":
            return "image/webp", KIND_IMAGE
        if subtype == b"WAVE":
            return "audio/wav", KIND_AUDIO
        if subtype == b"AVI ":
            return "video/x-msvideo", KIND_VIDEO

    if content.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm", KIND_VIDEO

    if content.startswith(b"ID3"):
        return "audio/mpeg", KIND_AUDIO
    if len(content) >= 2 and content[0] == 0xFF and (content[1] & 0xE0) == 0xE0:
        return "audio/mpeg", KIND_AUDIO

    if content.startswith(b"OggS"):
        return "audio/ogg", KIND_AUDIO
    if content.startswith(b"fLaC"):
        return "audio/flac", KIND_AUDIO

    return None, None

def _size_limit_for(kind: str) -> int:
    if kind == KIND_VIDEO:
        return settings.max_video_size
    if kind == KIND_AUDIO:
        return settings.max_audio_size
    return settings.max_upload_size

def save_post_file(post_id: int, content: bytes) -> tuple[str, str]:
    if len(content) == 0:
        raise ValidationError("El archivo esta vacio", field="file")

    mime, kind = _detect_media(content)

    if mime is None or kind is None:
        raise ValidationError(
            "Formato no reconocido. Se aceptan imagenes (JPG, PNG, WEBP, GIF), "
            "videos (MP4, WEBM, AVI) y audio (MP3, WAV, OGG, FLAC, M4A)",
            field="file",
        )

    limit = _size_limit_for(kind)
    if len(content) > limit:
        nombre = {KIND_IMAGE: "La imagen", KIND_VIDEO: "El video", KIND_AUDIO: "El audio"}[kind]
        raise ValidationError(
            f"{nombre} no puede pesar mas de {limit // (1024 * 1024)} MB", field="file"
        )

    extension = MEDIA_EXTENSIONS.get(mime, ".bin")

    safe_filename = f"{post_id}_{secrets.token_hex(8)}{extension}"
    destination: Path = settings.posts_dir / safe_filename

    with open(destination, "wb") as file_handle:
        file_handle.write(content)

    return f"/uploads/posts/{safe_filename}", kind

def delete_post_file(url: str) -> None:
    if not url:
        return

    file_path = settings.posts_dir / Path(url).name

    if file_path.is_file():
        file_path.unlink(missing_ok=True)
