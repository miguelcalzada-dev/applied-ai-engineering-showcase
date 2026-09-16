"""
rag_service.py - Servicio de Retrieval-Augmented Generation.
Usa LangChain + ChromaDB + embeddings de Google para indexar
y consultar documentos de texto o PDF.
"""

import os
import time
import uuid
from typing import Optional

from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document

# Chroma y embeddings de Google
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_community.vectorstores import Chroma
except ImportError:
    raise ImportError(
        "Asegurate de instalar langchain-google-genai para usar los embeddings de Google."
    )

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))

# Almacen en memoria: session_id -> vectordb
_stores: dict = {}
# Marca temporal de ultimo acceso por sesion (para la purga por TTL)
_last_seen: dict = {}
_request_count = 0

# Singleton del modelo de embeddings (tarda en cargar)
_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Retorna el modelo de embeddings (lo carga solo la primera vez)."""
    global _embeddings
    if _embeddings is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en las variables de entorno.")
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=api_key,
        )
    return _embeddings


def _sweep(now: float) -> None:
    """Elimina las sesiones RAG inactivas (nunca la demo)."""
    expired = [
        sid
        for sid, ts in _last_seen.items()
        if not sid.startswith("__") and now - ts > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _stores.pop(sid, None)
        _last_seen.pop(sid, None)


def _touch(session_id: str) -> None:
    """Marca la sesion como activa y purga periodicamente las caducadas."""
    global _request_count
    now = time.time()
    _last_seen[session_id] = now
    _request_count += 1
    if _request_count % 25 == 0:
        _sweep(now)


def create_store(text: str) -> str:
    """
    Indexa un texto en una nueva coleccion ChromaDB en memoria.

    Args:
        text: Texto completo del documento a indexar.

    Returns:
        session_id: Identificador unico de la sesion RAG.
    """
    session_id = str(uuid.uuid4())

    # Dividir en chunks para mejor recuperacion
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
    )
    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk) for chunk in chunks]

    embeddings = _get_embeddings()
    # Crear coleccion ChromaDB en memoria (sin persist_directory)
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=f"session_{session_id[:8]}",
    )
    _stores[session_id] = vectordb
    _touch(session_id)
    return session_id


def query_store(session_id: str, question: str, k: int = 4) -> str:
    """
    Recupera los fragmentos mas relevantes del indice para la pregunta.

    Args:
        session_id: ID de la sesion RAG.
        question: Pregunta del usuario.
        k: Numero de fragmentos a recuperar.

    Returns:
        Contexto concatenado de los k fragmentos mas relevantes.

    Raises:
        KeyError: Si el session_id no existe.
    """
    if session_id not in _stores:
        # El documento de demo es estatico: se reconstruye en el worker que atienda
        # la peticion (con varios workers de gunicorn cada uno tiene su propia memoria).
        if session_id == "__demo__":
            get_demo_session()
        else:
            raise KeyError(
                "Sesion no encontrada. Sube un documento primero o usa el documento de demo."
            )
    _touch(session_id)
    vectordb = _stores[session_id]
    docs = vectordb.similarity_search(question, k=k)
    context = "\n\n---\n\n".join([d.page_content for d in docs])
    return context


def get_demo_session() -> str:
    """
    Carga el documento de demo (sample_doc.txt) y retorna su session_id.
    Si ya esta cargado, reutiliza el existente.
    """
    demo_key = "__demo__"
    if demo_key in _stores:
        return demo_key

    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "sample_doc.txt"
    )
    data_path = os.path.normpath(data_path)

    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()

    real_id = create_store(text)
    # Guardar tambien con la clave especial __demo__
    _stores[demo_key] = _stores[real_id]
    _last_seen[demo_key] = time.time()
    return demo_key


def list_sessions() -> list:
    """Retorna los session_ids activos (excluye la demo interna)."""
    return [k for k in _stores if not k.startswith("__")]
