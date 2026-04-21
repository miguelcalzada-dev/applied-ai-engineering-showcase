"""
prompt_lab.py — Router del Laboratorio de Prompts.
Permite experimentar con system prompts, user prompts y temperatura,
devolviendo la respuesta del modelo junto con métricas de ejecución.
"""
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.gemini_service import run_prompt

router = APIRouter(prefix="/api/prompt-lab", tags=["Prompt Lab"])


class PromptLabRequest(BaseModel):
    system_prompt: Optional[str] = Field(
        default="",
        description="Instrucción de sistema que define el rol y comportamiento del modelo.",
    )
    user_prompt: str = Field(
        ...,
        description="Prompt del usuario / instrucción principal.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperatura del modelo (0=determinista, 1=muy creativo).",
    )


@router.post("")
async def run_prompt_lab(req: PromptLabRequest):
    """
    Ejecuta un prompt con parámetros configurables y devuelve
    la respuesta junto con métricas: latencia, tokens estimados,
    temperatura usada y recuento de palabras.
    """
    start_time = time.perf_counter()

    response_text = run_prompt(
        system=req.system_prompt or "",
        user=req.user_prompt,
        temperature=req.temperature,
    )

    elapsed = round(time.perf_counter() - start_time, 3)

    # Estimación rústica de tokens (≈ 1.3 tokens por palabra en español)
    input_words = len((req.system_prompt or "").split()) + len(req.user_prompt.split())
    output_words = len(response_text.split())
    est_input_tokens = int(input_words * 1.3)
    est_output_tokens = int(output_words * 1.3)

    return {
        "response": response_text,
        "metrics": {
            "latency_seconds": elapsed,
            "temperature": req.temperature,
            "estimated_input_tokens": est_input_tokens,
            "estimated_output_tokens": est_output_tokens,
            "output_words": output_words,
            "has_system_prompt": bool(req.system_prompt and req.system_prompt.strip()),
        },
    }
