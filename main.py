import os
import sys
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import chat, vision, rag, nlp, prompt_lab
from services.gemini_service import model_name

# Identidad del proceso: permite ver cuantas instancias/replicas hay detras.
_INSTANCE_ID = uuid.uuid4().hex[:8]
_STARTED_AT = time.time()


def _cmdline():
    """Linea de comandos con la que se arranco el proceso (Linux)."""
    try:
        with open("/proc/self/cmdline", "rb") as fh:
            return " ".join(
                part.decode("utf-8", "replace") for part in fh.read().split(b"\x00") if part
            )
    except OSError:
        return None

def _proc_status_mb(key: str):
    """Lee un valor de /proc/self/status en MB (Linux). None si no esta disponible."""
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith(key):
                    return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


def _rss_mb():
    """Memoria residente actual del proceso, en MB."""
    return _proc_status_mb("VmRSS:")


def _peak_rss_mb():
    """Pico historico de memoria residente del proceso, en MB."""
    return _proc_status_mb("VmHWM:")

app = FastAPI(
    title="AI Lab",
    description=(
        "Demo interactiva de capacidades de IA: Chat multi-turno, Vision por Computador, "
        "RAG con documentos propios, Laboratorio de Prompts, Herramientas NLP y Asistente de Voz."
    ),
    version="1.1.0",
    root_path="/ai-lab",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: solo el dominio propio (y local para desarrollo).
ALLOWED_ORIGINS = [
    "https://miguelcalzada.com",
    "https://www.miguelcalzada.com",
    "https://miguelcalzada.es",
    "https://www.miguelcalzada.es",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

# Archivos estaticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def redirect_legacy_root(request: Request, call_next):
    """
    La raiz de la URL antigua (Railway) redirige al dominio nuevo.
    Se usa raw_path (no reescrito) para NO afectar a las peticiones que llegan
    desde el portal a /ai-lab/... y evitar bucles de redireccion.
    """
    if request.scope.get("raw_path") in (b"/", b""):
        return RedirectResponse("https://miguelcalzada.com/ai-lab", status_code=308)
    return await call_next(request)


# Rate limiting basico en memoria para la API (protege la cuota de Gemini).
# Suficiente con 1 worker; con varias instancias haria falta un store compartido.
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_MAX", "40"))          # peticiones
_RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))  # por ventana de segundos
_rate_hits: dict = defaultdict(deque)


@app.middleware("http")
async def rate_limit_api(request: Request, call_next):
    if "/api/" in request.scope.get("path", ""):
        forwarded = request.headers.get("x-forwarded-for", "")
        ip = forwarded.split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        now = time.time()
        hits = _rate_hits[ip]
        while hits and now - hits[0] > _RATE_WINDOW:
            hits.popleft()
        if len(hits) >= _RATE_LIMIT:
            return JSONResponse(
                {"detail": "Demasiadas peticiones. Espera un momento e intentalo de nuevo."},
                status_code=429,
            )
        hits.append(now)
    return await call_next(request)


@app.get("/", include_in_schema=False)
async def serve_home():
    return FileResponse("static/index.html")


@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint de salud para Railway/Render y monitores."""
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY", "")),
        "model": model_name(),
        "rss_mb": _rss_mb(),
        "peak_rss_mb": _peak_rss_mb(),
        "instance": _INSTANCE_ID,
        "uptime_s": round(time.time() - _STARTED_AT),
        "cmdline": _cmdline(),
    }
