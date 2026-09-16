"""
gemini_service.py - Wrapper centralizado para Google Gemini API.

Usa el SDK unificado `google-genai` (el paquete `google-generativeai` esta
en fin de vida). Cubre: chat multi-turno, audio, analisis de imagenes y
prompts simples.
"""

import json
import os
import sys

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Modelo por defecto: rapido y economico. Configurable via GEMINI_MODEL.
DEFAULT_MODEL = "gemini-2.5-flash-lite"
_model_name: str = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

_client = None


def model_name() -> str:
    """Modelo activo (util para el endpoint /health)."""
    return _model_name


def _get_client():
    """Cliente Gemini perezoso (se crea en la primera llamada)."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY no esta configurada. "
                "Anade tu clave en el archivo .env (copialo desde .env.example)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _build_config(
    system: str = "",
    temperature: float = 0.7,
    json_mode: bool = False,
) -> types.GenerateContentConfig:
    """Construye la configuracion de generacion (system prompt, temperatura, JSON)."""
    return types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system.strip() or None,
        response_mime_type="application/json" if json_mode else None,
    )


def _to_content(message: dict) -> types.Content:
    """Convierte un mensaje propio {role, content} a un Content de Gemini."""
    role = message.get("role", "user")
    if role not in ("user", "model"):
        role = "user"
    return types.Content(role=role, parts=[types.Part(text=message.get("content", ""))])


def chat_response(
    history: list,
    user_message: str,
    system_prompt: str = "",
    temperature: float = 0.7,
) -> str:
    """
    Envia un mensaje con historial de conversacion y devuelve la respuesta.

    Args:
        history: Lista de dicts {"role": "user"|"model", "content": "..."}
                 con los mensajes anteriores de la sesion.
        user_message: Nuevo mensaje del usuario.
        system_prompt: Instruccion de sistema opcional.
        temperature: Temperatura del modelo (0=determinista, 1=creativo).

    Returns:
        Texto de la respuesta del modelo.
    """
    client = _get_client()
    chat = client.chats.create(
        model=_model_name,
        config=_build_config(system_prompt, temperature),
        history=[_to_content(msg) for msg in history],
    )
    response = chat.send_message(user_message)
    return response.text


def voice_response(
    history: list,
    audio_bytes: bytes,
    mime_type: str,
    system_prompt: str = "",
    temperature: float = 0.7,
) -> tuple:
    """
    Envia un mensaje de audio con historial y obtiene la transcripcion y la respuesta.
    Devuelve una tupla (transcript, response).
    """
    client = _get_client()

    json_instruction = (
        "El usuario te ha enviado un mensaje de voz.\n"
        "1. Transcribe exactamente lo que el usuario dijo.\n"
        "2. Responde al mensaje del usuario, siguiendo tus instrucciones de rol.\n"
        "Debes devolver un objeto JSON estricto con las claves 'transcript' (texto) "
        "y 'response' (texto)."
    )
    combined_system = (
        f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction
    )

    chat = client.chats.create(
        model=_model_name,
        config=_build_config(combined_system, temperature, json_mode=True),
        history=[_to_content(msg) for msg in history],
    )

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    try:
        response = chat.send_message(
            [
                types.Part.from_text(text="(Mensaje de voz del usuario)"),
                audio_part,
            ]
        )
        data = json.loads(response.text)
        transcript = data.get("transcript", "")
        reply = data.get("response", "")
        if not transcript or not reply:
            raise ValueError("Faltan campos 'transcript'/'response' en el JSON")
        return transcript, reply
    except Exception as exc:  # noqa: BLE001 - se degrada de forma controlada
        print(f"Error en voice_response: {exc}", file=sys.stderr)
        return (
            "Audio ininteligible o error de procesamiento.",
            "Lo siento, no pude procesar el audio correctamente.",
        )


def analyze_image(
    image_bytes: bytes,
    question: str,
    mime_type: str = "image/jpeg",
) -> str:
    """
    Analiza una imagen con Gemini Vision y responde a la pregunta dada.

    Lanza RuntimeError si el modelo no puede procesar la imagen, para que el
    router pueda devolver un error HTTP adecuado.
    """
    client = _get_client()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    full_question = question.strip() + ". Responde siempre en espanol."

    try:
        response = client.models.generate_content(
            model=_model_name,
            contents=[full_question, image_part],
            config=types.GenerateContentConfig(temperature=0.5),
        )
        return response.text
    except Exception as exc:  # noqa: BLE001 - se re-lanza con contexto
        print(f"Error en analyze_image: {exc}", file=sys.stderr)
        raise RuntimeError(
            "No se pudo procesar la imagen con Gemini. "
            "Es posible que el servicio este saturado o la imagen sea demasiado compleja."
        ) from exc


def run_prompt(system: str, user: str, temperature: float = 0.7) -> str:
    """
    Ejecuta un prompt simple (con o sin system instruction).
    Usado por Prompt Lab, NLP Tools y RAG para generar respuestas.

    Args:
        system: Instruccion de sistema / rol del asistente.
        user: Prompt del usuario.
        temperature: Temperatura del modelo.

    Returns:
        Texto de la respuesta.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=_model_name,
        contents=user,
        config=_build_config(system, temperature),
    )
    return response.text
