"""
chat.py - Router de Chat multi-turno con Gemini.
Mantiene el historial de sesion en memoria del servidor con expiracion (TTL).
"""

import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from services.gemini_service import chat_response, voice_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Almacen de sesiones: session_id -> lista de mensajes
_sessions: dict = {}
_last_seen: dict = {}
_request_count = 0

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
_SWEEP_EVERY = 25


def _sweep(now: float) -> None:
    """Elimina las sesiones inactivas para evitar fugas de memoria."""
    expired = [sid for sid, ts in _last_seen.items() if now - ts > SESSION_TTL_SECONDS]
    for sid in expired:
        _sessions.pop(sid, None)
        _last_seen.pop(sid, None)


def _touch(session_id: str) -> None:
    """Marca la sesion como activa y purga periodicamente las caducadas."""
    global _request_count
    now = time.time()
    _last_seen[session_id] = now
    _request_count += 1
    if _request_count % _SWEEP_EVERY == 0:
        _sweep(now)


def _get_history(session_id: str) -> list:
    _touch(session_id)
    return _sessions.setdefault(session_id, [])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    system_prompt: Optional[str] = ""
    temperature: float = 0.7


class ChatResponse(BaseModel):
    session_id: str
    response: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Envia un mensaje al chat y recibe respuesta de Gemini.
    Si no se provee session_id, se crea una nueva sesion.
    El historial se mantiene automaticamente en el servidor.
    """
    session_id = req.session_id or str(uuid.uuid4())
    history = _get_history(session_id)

    response_text = chat_response(
        history=history,
        user_message=req.message,
        system_prompt=req.system_prompt or "",
        temperature=req.temperature,
    )

    # Anadir al historial despues de obtener la respuesta
    history.append({"role": "user", "content": req.message})
    history.append({"role": "model", "content": response_text})

    return {"session_id": session_id, "response": response_text}


@router.post("/voice")
async def chat_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(""),
    temperature: float = Form(0.7),
):
    """
    Recibe un mensaje de voz, lo transcribe y responde usando Gemini Audio.
    El historial se mantiene igual que en el chat de texto.
    """
    sess_id = session_id or str(uuid.uuid4())
    history = _get_history(sess_id)

    audio_bytes = await audio.read()

    # Enviar a Gemini para transcripcion y respuesta
    transcript, response_text = voice_response(
        history=history,
        audio_bytes=audio_bytes,
        mime_type=audio.content_type,
        system_prompt=system_prompt or "",
        temperature=temperature,
    )

    # Anadir al historial de la sesion
    history.append({"role": "user", "content": transcript})
    history.append({"role": "model", "content": response_text})

    return {
        "session_id": sess_id,
        "transcript": transcript,
        "response": response_text,
    }


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Limpia el historial de una sesion de chat."""
    _sessions.pop(session_id, None)
    _last_seen.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@router.get("/{session_id}/history")
async def get_history(session_id: str):
    """Obtiene el historial completo de una sesion."""
    history = _sessions.get(session_id, [])
    return {"session_id": session_id, "history": history, "messages": len(history)}
