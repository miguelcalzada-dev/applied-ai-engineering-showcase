"""
gemini_service.py — Wrapper centralizado para Google Gemini API.
Cubre: chat multi-turno, análisis de imágenes y prompts simples.
"""
import os
import io

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_api_key: str = os.getenv("GEMINI_API_KEY", "")
_model_name: str = "gemini-2.5-flash-lite"

genai.configure(api_key=_api_key)


def _ensure_key() -> None:
    if not _api_key:
        raise ValueError(
            "GEMINI_API_KEY no está configurada. "
            "Añade tu clave en el archivo .env (cópialo desde .env.example)."
        )


def _build_model(system: str = "", temperature: float = 0.7, json_mode: bool = False) -> genai.GenerativeModel:
    """Construye un GenerativeModel con el system prompt e instrucciones dadas."""
    kwargs: dict = {}
    
    config = genai.types.GenerationConfig(temperature=temperature)
    if json_mode:
        config.response_mime_type = "application/json"
    
    kwargs["generation_config"] = config
        
    if system and system.strip():
        kwargs["system_instruction"] = system.strip()
    return genai.GenerativeModel(_model_name, **kwargs)


def chat_response(
    history: list,
    user_message: str,
    system_prompt: str = "",
    temperature: float = 0.7,
) -> str:
    """
    Envía un mensaje con historial de conversación y devuelve la respuesta.
    
    Args:
        history: Lista de dicts {"role": "user"|"model", "content": "..."}
                 con los mensajes anteriores de la sesión.
        user_message: Nuevo mensaje del usuario.
        system_prompt: Instrucción de sistema opcional.
        temperature: Temperatura del modelo (0=determinista, 1=creativo).
    
    Returns:
        Texto de la respuesta del modelo.
    """
    _ensure_key()

    # Convertir historial propio → formato Gemini
    gemini_history = [
        {"role": msg["role"], "parts": [msg["content"]]}
        for msg in history
    ]

    model = _build_model(system=system_prompt, temperature=temperature)
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(user_message)
    return response.text


def voice_response(
    history: list,
    audio_bytes: bytes,
    mime_type: str,
    system_prompt: str = "",
    temperature: float = 0.7,
) -> tuple[str, str]:
    """
    Envía un mensaje de audio con historial, obtiene la transcripción y la respuesta en JSON.
    """
    _ensure_key()
    import json

    gemini_history = [
        {"role": msg["role"], "parts": [msg["content"]]}
        for msg in history
    ]

    json_instruction = (
        "El usuario te ha enviado un mensaje de voz.\n"
        "1. Transcribe exactamente lo que el usuario dijo.\n"
        "2. Responde al mensaje del usuario, siguiendo tus instrucciones de rol.\n"
        "Debes devolver un objeto JSON estricto con las claves 'transcript' (texto) y 'response' (texto)."
    )
    combined_system = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction

    model = _build_model(system=combined_system, temperature=temperature, json_mode=True)
    chat = model.start_chat(history=gemini_history)

    audio_part = {
        "mime_type": mime_type,
        "data": audio_bytes
    }

    try:
        response = chat.send_message(["(Mensaje de voz del usuario)", audio_part])
        data = json.loads(response.text)
        transcript = data.get("transcript", "")
        reply = data.get("response", "")
        if not transcript or not reply:
             raise ValueError("Faltan campos en el JSON")
        return transcript, reply
    except Exception as e:
        return "Audio ininteligible o error de procesamiento.", "Lo siento, no pude procesar el audio correctamente."



def analyze_image(image_bytes: bytes, question: str, mime_type: str = "image/jpeg") -> str:
    """
    Analiza una imagen con Gemini Vision y responde a la pregunta dada.
    """
    _ensure_key()
    model = _build_model(temperature=0.5)
    
    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }
    
    full_question = question.strip() + ". Responde siempre en español."
    try:
        response = model.generate_content([full_question, image_part])
        return response.text
    except Exception as e:
        import sys
        print(f"Error in analyze_image: {e}", file=sys.stderr)
        return "Hubo un error al procesar la imagen con Gemini. Es posible que el servicio esté saturado o la imagen sea demasiado compleja."


def run_prompt(system: str, user: str, temperature: float = 0.7) -> str:
    """
    Ejecuta un prompt simple (con o sin system instruction).
    Usado por Prompt Lab, NLP Tools y RAG para generar respuestas.
    
    Args:
        system: Instrucción de sistema / rol del asistente.
        user: Prompt del usuario.
        temperature: Temperatura del modelo.
    
    Returns:
        Texto de la respuesta.
    """
    _ensure_key()
    model = _build_model(system=system, temperature=temperature)
    response = model.generate_content(user)
    return response.text
