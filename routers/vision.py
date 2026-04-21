"""
vision.py — Router de Análisis de Imágenes con Gemini Vision.
Acepta imágenes desde upload de archivo.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.gemini_service import analyze_image

router = APIRouter(prefix="/api/vision", tags=["Vision"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 10


@router.post("")
async def vision_analyze(
    image: UploadFile = File(..., description="Imagen a analizar (JPEG, PNG, WEBP)"),
    question: str = Form(
        default="¿Qué ves en esta imagen? Describe todo con el máximo detalle posible.",
        description="Pregunta o instrucción sobre la imagen.",
    ),
):
    """
    Analiza una imagen con Gemini Vision y responde a la pregunta.
    Soporta imágenes subidas desde disco o capturadas desde webcam (como Blob).
    """
    # Validar tipo de archivo
    content_type = image.content_type or ""
    if content_type not in ALLOWED_MIME and not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {content_type}. Usa JPEG, PNG o WEBP.",
        )

    image_bytes = await image.read()

    # Validar tamaño
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Imagen demasiado grande ({size_mb:.1f} MB). Máximo {MAX_SIZE_MB} MB.",
        )

    result = analyze_image(image_bytes=image_bytes, question=question)
    return {
        "result": result,
        "filename": image.filename,
        "size_kb": round(len(image_bytes) / 1024, 1),
    }
