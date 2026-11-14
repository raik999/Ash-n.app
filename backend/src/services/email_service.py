from __future__ import annotations

import logging
import smtplib

from email.message import EmailMessage

from config.settings import settings

logger = logging.getLogger("ashun")

def esta_configurado() -> bool:
    return bool(settings.smtp_host and settings.smtp_username)

def _remitente() -> str:
    return settings.smtp_from or settings.smtp_username or "ashun@localhost"

def enviar(destinatarios: list[str], asunto: str, cuerpo: str) -> bool:
    limpios = [d.strip() for d in destinatarios if d and d.strip()]
    if not limpios:
        return False

    mensaje = EmailMessage()
    mensaje["From"] = _remitente()
    mensaje["To"] = ", ".join(limpios)
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    if not esta_configurado():
        _imprimir(mensaje, limpios)
        return True

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as servidor:
            if settings.smtp_use_tls:
                servidor.starttls()
            if settings.smtp_password:
                servidor.login(settings.smtp_username, settings.smtp_password)
            servidor.send_message(mensaje)
    except Exception as error:
        logger.warning("No se pudo enviar el correo a %s: %s", limpios, error)
        return False

    logger.info("Correo enviado a %s: %s", limpios, asunto)
    return True

def _imprimir(mensaje: EmailMessage, destinatarios: list[str]) -> None:
    linea = "=" * 70
    logger.info(
        "\n%s\nCORREO (no enviado: falta configurar SMTP en el .env)\n%s\n"
        "Para:    %s\nAsunto:  %s\n\n%s\n%s",
        linea,
        linea,
        ", ".join(destinatarios),
        mensaje["Subject"],
        mensaje.get_content().strip(),
        linea,
    )

FIRMA = "\n\n--\nAshun, la red social de artistas."

def aviso_de_sancion(
    nombre: str,
    dias: int,
    hasta: str,
    motivo: str | None,
) -> tuple[str, str]:
    explicacion = f"\n\nMotivo indicado: {motivo}" if motivo else ""

    plural = "dia" if dias == 1 else "dias"

    return (
        "Tu cuenta de Ashun fue suspendida temporalmente",
        f"Hola {nombre}:\n\n"
        f"Un administrador suspendio tu cuenta por {dias} {plural}. "
        f"Vas a poder volver a entrar a partir del {hasta}."
        f"{explicacion}\n\n"
        "Mientras dure la suspension no vas a poder iniciar sesion. "
        "Tus publicaciones y tus mensajes siguen guardados."
        f"{FIRMA}",
    )

def aviso_de_publicacion_eliminada(
    nombre: str,
    titulo: str | None,
    descripcion: str | None,
) -> tuple[str, str]:
    referencia = (titulo or descripcion or "").strip()
    if len(referencia) > 80:
        referencia = referencia[:77] + "..."

    cual = f'\n\nSe trataba de: "{referencia}"' if referencia else ""

    return (
        "Un administrador elimino una de tus publicaciones",
        f"Hola {nombre}:\n\n"
        "Un administrador de Ashun elimino una de tus publicaciones por no "
        "cumplir con las normas de la comunidad."
        f"{cual}\n\n"
        "Tu cuenta sigue activa y podes seguir publicando."
        f"{FIRMA}",
    )

def aviso_de_reporte(
    quien_reporta: str,
    que_es: str,
    detalle: str,
    motivo: str | None,
) -> tuple[str, str]:
    explicacion = f"\n\nMotivo que escribio: {motivo}" if motivo else ""

    return (
        f"Reporte nuevo en Ashun: {que_es}",
        f"@{quien_reporta} reporto {que_es}.\n\n"
        f"{detalle}"
        f"{explicacion}\n\n"
        "Entra a Ashun para revisarlo."
        f"{FIRMA}",
    )

def aviso_de_cuenta_eliminada(nombre: str) -> tuple[str, str]:
    return (
        "Tu cuenta de Ashun fue eliminada",
        f"Hola {nombre}:\n\n"
        "Un administrador elimino tu cuenta de Ashun por no cumplir con las "
        "normas de la comunidad.\n\n"
        "Tus publicaciones, comentarios y conversaciones se eliminaron junto "
        "con ella. Esta accion no se puede deshacer."
        f"{FIRMA}",
    )
