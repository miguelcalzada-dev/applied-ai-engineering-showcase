import os
import sys

# Logs de diagnóstico para Render
print(">>> [STARTUP] Iniciando Applied AI Engineering Showcase...", file=sys.stderr)
sys.stderr.flush()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
print(f">>> [STARTUP] Python versión: {sys.version}", file=sys.stderr)
print(f">>> [STARTUP] Directorio actual: {os.getcwd()}", file=sys.stderr)
sys.stderr.flush()

from routers import chat, vision, rag, nlp, prompt_lab

app = FastAPI(
    title="AI Portfolio Demo",
    description=(
        "Demo interactiva de capacidades de IA: Chat multi-turno, Visión por Computador, "
        "RAG con documentos propios, Laboratorio de Prompts, Herramientas NLP y Asistente de Voz."
    ),
    version="1.0.0",
    root_path="/ai-lab",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS para desarrollo local y despliegue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de la API
app.include_router(chat.router)
app.include_router(vision.router)
app.include_router(rag.router)
app.include_router(nlp.router)
app.include_router(prompt_lab.router)

# Archivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def redirect_legacy_root(request: Request, call_next):
    """
    La raíz de la URL antigua (Railway) redirige al dominio nuevo.
    Se usa raw_path (no reescrito) para NO afectar a las peticiones que llegan
    desde el portal a /ai-lab/... y evitar bucles de redirección.
    """
    if request.scope.get("raw_path") in (b"/", b""):
        return RedirectResponse("https://miguelcalzada.com/ai-lab", status_code=308)
    return await call_next(request)


@app.get("/", include_in_schema=False)
async def serve_home():
    return FileResponse("static/index.html")


@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint de salud para Railway/Render y monitores."""
    api_key_set = bool(os.getenv("GEMINI_API_KEY", ""))
    return {
        "status": "ok",
        "api_key_configured": api_key_set,
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    }
