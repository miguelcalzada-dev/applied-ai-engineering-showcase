"""
rag.py — Router de RAG (Retrieval-Augmented Generation).
Permite subir documentos (.txt, .pdf), indexarlos con ChromaDB
y hacer preguntas respondidas exclusivamente con el contenido del documento.
"""
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.rag_service import create_store, query_store, get_demo_session
from services.gemini_service import run_prompt

router = APIRouter(prefix="/api/rag", tags=["RAG"])


class RagQuery(BaseModel):
    session_id: str
    question: str


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Sube un documento (.txt o .pdf), lo indexa en ChromaDB y devuelve
    un session_id para usarlo en las consultas posteriores.
    """
    content = await file.read()
    filename = file.filename or ""

    if filename.lower().endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error leyendo PDF: {e}")
    else:
        # Tratar como texto plano
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="ignore")

    if not text.strip():
        raise HTTPException(status_code=400, detail="El documento está vacío o no se pudo leer el texto.")

    session_id = create_store(text)
    return {
        "session_id": session_id,
        "filename": filename,
        "chars": len(text),
        "words": len(text.split()),
    }


@router.get("/demo")
async def use_demo():
    """
    Carga el documento de demo (Guía de IA) y devuelve su session_id.
    Útil para probar el RAG sin necesidad de subir un archivo.
    """
    session_id = get_demo_session()
    return {
        "session_id": session_id,
        "message": "Documento de demo cargado: 'Guía de Tecnologías de IA'",
    }


@router.post("/query")
async def query_rag(req: RagQuery):
    """
    Busca en el documento indexado los fragmentos más relevantes
    para la pregunta y genera una respuesta fundamentada.
    """
    try:
        context = query_store(req.session_id, req.question, k=4)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    system = (
        "Eres un asistente experto en análisis de documentos. "
        "Dispones del siguiente contexto extraído de un documento:\n\n"
        f"{context}\n\n"
        "Responde ÚNICAMENTE basándote en el contexto proporcionado. "
        "Si la información solicitada no aparece en el contexto, indícalo claramente. "
        "Responde en español, de forma clara, estructurada y concisa."
    )
    response = run_prompt(system=system, user=req.question, temperature=0.4)

    return {
        "response": response,
        "context_used": context,
        "session_id": req.session_id,
    }
