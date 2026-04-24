"""
chat.py — Router de Chat multi-turno con Gemini.
Mantiene historial de sesión en memoria del servidor.
"""
import uuid
from services.gemini_service import chat_response, voice_response
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Almacén de sesiones: session_id → lista de mensajes
_sessions: dict = {}


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
    Envía un mensaje al chat y recibe respuesta de Gemini.
    Si no se provee session_id, se crea una nueva sesión.
    El historial se mantiene automáticamente en el servidor.
    """
    session_id = req.session_id or str(uuid.uuid4())

    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]

    response_text = chat_response(
        history=history,
        user_message=req.message,
        system_prompt=req.system_prompt or "",
        temperature=req.temperature,
    )

    # Añadir al historial después de obtener la respuesta
    history.append({"role": "user", "content": req.message})
    history.append({"role": "model", "content": response_text})

    return {"session_id": session_id, "response": response_text}


@router.post("/voice")
async def chat_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(""),
    temperature: float = Form(0.7)
):
    """
    Recibe un mensaje de voz, lo transcribe y responde usando Gemini Audio.
    El historial se mantiene igual que en el chat de texto.
    """
    sess_id = session_id or str(uuid.uuid4())
    
    if sess_id not in _sessions:
        _sessions[sess_id] = []
        
    history = _sessions[sess_id]
    
    audio_bytes = await audio.read()
    
    # Enviar a Gemini para transcripción y respuesta
    transcript, response_text = voice_response(
        history=history,
        audio_bytes=audio_bytes,
        mime_type=audio.content_type,
        system_prompt=system_prompt or "",
        temperature=temperature
    )
    
    # Añadir al historial de la sesión
    history.append({"role": "user", "content": transcript})
    history.append({"role": "model", "content": response_text})
    
    return {
        "session_id": sess_id,
        "transcript": transcript,
        "response": response_text
    }


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Limpia el historial de una sesión de chat."""
    _sessions.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@router.get("/{session_id}/history")
async def get_history(session_id: str):
    """Obtiene el historial completo de una sesión."""
    history = _sessions.get(session_id, [])
    return {"session_id": session_id, "history": history, "messages": len(history)}
