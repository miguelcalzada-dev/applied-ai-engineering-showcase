"""
rag_service.py — Servicio de Retrieval-Augmented Generation.
Usa LangChain + ChromaDB + HuggingFace Embeddings para indexar
y consultar documentos de texto o PDF.
"""
import os
import uuid
from typing import Optional

from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document

# Importar Chroma y embeddings desde langchain_community
# Importar Chroma y embeddings de Google
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_community.vectorstores import Chroma
except ImportError:
    # Fallback o mensaje de error si no está instalado
    raise ImportError("Asegúrate de instalar langchain-google-genai para usar embeddings de Google.")

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

# Almacén en memoria: session_id → vectordb
_stores: dict = {}

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
            google_api_key=api_key
        )
    return _embeddings


def create_store(text: str) -> str:
    """
    Indexa un texto en una nueva colección ChromaDB en memoria.
    
    Args:
        text: Texto completo del documento a indexar.
    
    Returns:
        session_id: Identificador único de la sesión RAG.
    """
    session_id = str(uuid.uuid4())

    # Dividir en chunks para mejor recuperación
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
    )
    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk) for chunk in chunks]

    embeddings = _get_embeddings()
    # Crear colección ChromaDB en memoria (sin persist_directory)
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=f"session_{session_id[:8]}",
    )
    _stores[session_id] = vectordb
    return session_id


def query_store(session_id: str, question: str, k: int = 4) -> str:
    """
    Recupera los fragmentos más relevantes del índice para la pregunta.
    
    Args:
        session_id: ID de la sesión RAG.
        question: Pregunta del usuario.
        k: Número de fragmentos a recuperar.
    
    Returns:
        Contexto concatenado de los k fragmentos más relevantes.
    
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
                "Sesión no encontrada. Sube un documento primero o usa el documento de demo."
            )
    vectordb = _stores[session_id]
    docs = vectordb.similarity_search(question, k=k)
    context = "\n\n---\n\n".join([d.page_content for d in docs])
    return context


def get_demo_session() -> str:
    """
    Carga el documento de demo (sample_doc.txt) y retorna su session_id.
    Si ya está cargado, reutiliza el existente.
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
    # Guardar también con la clave especial __demo__
    _stores[demo_key] = _stores[real_id]
    return demo_key


def list_sessions() -> list:
    """Retorna los session_ids activos (excluye la demo interna)."""
    return [k for k in _stores if not k.startswith("__")]
