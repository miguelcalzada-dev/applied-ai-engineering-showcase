"""
gemini_service.py — Wrapper centralizado para Google Gemini API.
Cubre: chat multi-turno, análisis de imágenes y prompts simples.
"""
import os
import io

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

_api_key: str = os.getenv("GEMINI_API_KEY", "")
_model_name: str = "gemini-2.5-flash"

genai.configure(api_key=_api_key)


def _ensure_key() -> None:
    if not _api_key:
        raise ValueError(
            "GEMINI_API_KEY no está configurada. "
            "Añade tu clave en el archivo .env (cópialo desde .env.example)."
        )


def _build_model(system: str = "", temperature: float = 0.7) -> genai.GenerativeModel:
    """Construye un GenerativeModel con el system prompt e instrucciones dadas."""
    kwargs: dict = {
        "generation_config": genai.types.GenerationConfig(temperature=temperature)
    }
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


def analyze_image(image_bytes: bytes, question: str) -> str:
    """
    Analiza una imagen con Gemini Vision y responde a la pregunta dada.
    
    Args:
        image_bytes: Bytes de la imagen (JPEG, PNG, WEBP...).
        question: Pregunta o prompt sobre la imagen.
    
    Returns:
        Respuesta textual del modelo sobre la imagen.
    """
    _ensure_key()
    model = _build_model(temperature=0.5)
    image = Image.open(io.BytesIO(image_bytes))
    full_question = question.strip() + ". Responde siempre en español."
    response = model.generate_content([full_question, image])
    return response.text


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
