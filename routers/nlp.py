"""
nlp.py — Router de Herramientas NLP.
Expone tres endpoints independientes:
  - /sentiment  → Análisis de sentimiento con JSON estructurado
  - /summarize  → Resumen automático de texto
  - /classify   → Clasificación de intención y categoría
"""
import json
import re
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.gemini_service import run_prompt

router = APIRouter(prefix="/api/nlp", tags=["NLP Tools"])


class NLPRequest(BaseModel):
    text: str
    max_words: Optional[int] = 80  # Solo usado en /summarize


def _extract_json(raw: str) -> dict:
    """Extrae el primer objeto JSON de una respuesta de texto."""
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"raw": raw}


@router.post("/sentiment")
async def sentiment_analysis(req: NLPRequest):
    """
    Analiza el sentimiento del texto.
    Devuelve: sentiment, score, emotions, keywords, explanation.
    """
    system = """Eres un experto en Procesamiento de Lenguaje Natural (NLP) y análisis de sentimientos.
Analiza el texto del usuario y devuelve ÚNICAMENTE un objeto JSON con exactamente esta estructura:
{
  "sentiment": "positivo|negativo|neutro|mixto",
  "score": <número de -1.0 a 1.0, donde -1 es muy negativo y 1 muy positivo>,
  "confidence": <número de 0.0 a 1.0>,
  "emotions": ["lista", "de", "emociones", "detectadas"],
  "keywords": ["palabras", "clave", "importantes"],
  "explanation": "Explicación breve del análisis (máximo 2 frases)"
}
Solo devuelve el JSON, absolutamente nada más."""

    result = run_prompt(system=system, user=req.text, temperature=0.2)
    return _extract_json(result)


@router.post("/summarize")
async def summarize(req: NLPRequest):
    """
    Resume el texto en el número de palabras indicado.
    """
    max_w = req.max_words or 80
    system = f"""Eres un experto en resumen y síntesis de texto.
Resume el siguiente texto en un máximo de {max_w} palabras.
El resumen debe:
- Estar en español
- Capturar los puntos más importantes
- Ser fluido y natural
- NO incluir frases introductorias como "El texto habla de..." o "En resumen..."

Devuelve ÚNICAMENTE el resumen, nada más."""

    result = run_prompt(system=system, user=req.text, temperature=0.4)
    word_count = len(result.split())
    return {"summary": result.strip(), "words": word_count}


@router.post("/classify")
async def classify_intent(req: NLPRequest):
    """
    Clasifica la intención, categoría, tono e idioma del texto.
    """
    system = """Eres un experto en clasificación de texto y análisis lingüístico (NLP).
Clasifica el texto del usuario y devuelve ÚNICAMENTE un objeto JSON con esta estructura exacta:
{
  "intent": "pregunta|afirmación|queja|petición|saludo|opinión|instrucción|otro",
  "category": "categoría temática del texto (p.ej: tecnología, política, salud...)",
  "confidence": <0.0 a 1.0>,
  "language": "idioma detectado (p.ej: español, inglés, francés...)",
  "tone": "formal|informal|técnico|emocional|neutro|agresivo",
  "is_question": <true|false>,
  "subjectivity": "objetivo|subjetivo|mixto",
  "explanation": "Explicación breve de la clasificación (máximo 2 frases)"
}
Solo devuelve el JSON, absolutamente nada más."""

    result = run_prompt(system=system, user=req.text, temperature=0.2)
    return _extract_json(result)
