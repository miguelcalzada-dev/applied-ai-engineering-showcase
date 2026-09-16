"""
vision.py - Router de Analisis de Imagenes con Gemini Vision.
Acepta imagenes desde upload de archivo.
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
        default="Que ves en esta imagen? Describe todo con el maximo detalle posible.",
        description="Pregunta o instruccion sobre la imagen.",
    ),
):
    """
    Analiza una imagen con Gemini Vision y responde a la pregunta.
    Soporta imagenes subidas desde disco o capturadas desde webcam (como Blob).
    """
    # Validar tipo de archivo
    content_type = image.content_type or ""
    if content_type not in ALLOWED_MIME and not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {content_type}. Usa JPEG, PNG o WEBP.",
        )

    image_bytes = await image.read()

    # Validar tamano
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Imagen demasiado grande ({size_mb:.1f} MB). Maximo {MAX_SIZE_MB} MB.",
        )

    try:
        result = analyze_image(
            image_bytes=image_bytes,
            question=question,
            mime_type=content_type,
        )
    except RuntimeError as exc:
        # Error controlado del servicio (servicio saturado, imagen no procesable...)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "result": result,
        "filename": image.filename,
        "size_kb": round(len(image_bytes) / 1024, 1),
    }
