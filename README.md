# Applied AI Engineering Showcase

[![CI](https://github.com/miguelcalzada-dev/applied-ai-engineering-showcase/actions/workflows/ci.yml/badge.svg)](https://github.com/miguelcalzada-dev/applied-ai-engineering-showcase/actions/workflows/ci.yml)
[![Live](https://img.shields.io/badge/demo-miguelcalzada.com%2Fai--lab-6366f1?style=flat-square)](https://miguelcalzada.com/ai-lab)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)

Aplicación web interactiva que reúne los casos de uso de IA más demandados en la industria —**LLMs**, **RAG**, **visión por computador** y **NLP**— en una suite unificada, con backend **FastAPI** y una interfaz **brutalista/editorial** en Vanilla JS/CSS.

**Demo en producción:** <https://miguelcalzada.com/ai-lab>

---

## Tabla de contenidos

- [Módulos](#módulos)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Puesta en marcha](#puesta-en-marcha)
- [Variables de entorno](#variables-de-entorno)
- [API](#api)
- [Estructura](#estructura)
- [Autor](#autor)
- [Licencia](#licencia)

---

## Módulos

1. **Chat multi-turno (LLM Core)** — conversaciones con memoria de contexto, *system prompt* y temperatura ajustables, transcripción y envío de voz (MediaRecorder).
2. **Análisis de imágenes (Vision)** — subida por *drag & drop* o captura desde webcam, analizadas con Gemini Vision.
3. **RAG (Retrieval-Augmented Generation)** — carga de documentos `.txt`/`.pdf`, vectorización y búsqueda semántica con **LangChain**, embeddings de Google y **ChromaDB**, con acordeón para auditar los fragmentos recuperados.
4. **Laboratorio de Prompts** — testeo de roles y configuraciones avanzadas con métricas de latencia, tokens estimados y recuento de palabras.
5. **NLP Tools** — análisis de sentimiento, resumen de texto y clasificación de intención/idioma/tono.
6. **Asistente de voz** — interfaz "manos libres" con Speech-to-Text y Text-to-Speech nativos de Gemini.

## Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Backend | FastAPI · Pydantic · Uvicorn/Gunicorn |
| IA / LLM | Google Gemini (`gemini-2.5-flash-lite` por defecto) vía SDK `google-genai` |
| RAG | LangChain · ChromaDB · embeddings de Google |
| Frontend | SPA en Vanilla JavaScript y CSS (glassmorphism, dark mode) |
| Despliegue | Railway (Nixpacks + Procfile) |
| Observabilidad | Endpoint `/health`, rate limiting por IP, logging a stderr |

## Arquitectura

```text
Navegador (SPA Vanilla JS)
   │  fetch /api/*
   ▼
FastAPI (main.py)
   ├── /api/chat       → Gemini (texto y voz)
   ├── /api/vision     → Gemini Vision
   ├── /api/rag        → ChromaDB + embeddings + Gemini
   ├── /api/nlp        → Gemini (JSON estructurado)
   └── /api/prompt-lab → Gemini (métricas de ejecución)
```

- **Sesiones en memoria con TTL:** los historiales de chat y los índices RAG se guardan por `session_id` y se purgan automáticamente tras `SESSION_TTL_SECONDS` de inactividad para evitar fugas de memoria.
- **Rate limiting por IP** para proteger la cuota de Gemini.
- **CORS** restringido a los dominios propios y a `localhost`.
- El despliegue usa **1 worker** de Gunicorn (el estado es en memoria). Para escalar horizontalmente, sustituir las sesiones por un store compartido (Redis) y el rate limit por un backend distribuido.

## Puesta en marcha

Requisitos: **Python 3.11+**.

```bash
# 1. Entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env            # edita y añade GEMINI_API_KEY

# 4. Servidor
uvicorn main:app --reload
```

- Aplicación: <http://localhost:8000>
- Documentación interactiva: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

Consigue una API key gratuita en [Google AI Studio](https://aistudio.google.com/apikey).

## Variables de entorno

Todas están documentadas en [`.env.example`](./.env.example).

| Variable | Descripción | Por defecto |
| --- | --- | --- |
| `GEMINI_API_KEY` | Clave de la API de Google Gemini (**obligatoria**). | — |
| `GEMINI_MODEL` | Modelo Gemini a usar. | `gemini-2.5-flash-lite` |
| `GEMINI_EMBEDDING_MODEL` | Modelo de embeddings para el RAG. | `models/gemini-embedding-001` |
| `PORT` | Puerto del servidor. | `8000` |
| `SESSION_TTL_SECONDS` | TTL de las sesiones en memoria (chat y RAG). | `3600` |
| `RATE_LIMIT_MAX` | Máximo de peticiones por IP en la ventana. | `40` |
| `RATE_LIMIT_WINDOW_SECONDS` | Ventana del rate limit, en segundos. | `60` |

## API

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `POST` | `/api/chat` | Chat multi-turno. |
| `POST` | `/api/chat/voice` | Chat por voz (transcripción + respuesta). |
| `GET` | `/api/chat/{session_id}/history` | Historial de una sesión. |
| `DELETE` | `/api/chat/{session_id}` | Limpia una sesión. |
| `POST` | `/api/vision` | Análisis de imágenes. |
| `POST` | `/api/rag/upload` | Indexa un documento `.txt`/`.pdf`. |
| `GET` | `/api/rag/demo` | Carga el documento de demo. |
| `POST` | `/api/rag/query` | Pregunta sobre un documento indexado. |
| `POST` | `/api/nlp/sentiment` | Análisis de sentimiento. |
| `POST` | `/api/nlp/summarize` | Resumen de texto. |
| `POST` | `/api/nlp/classify` | Clasificación de intención. |
| `POST` | `/api/prompt-lab` | Laboratorio de prompts con métricas. |
| `GET` | `/health` | Estado del servicio y modelo activo. |

## Estructura

```text
main.py                 # App FastAPI, CORS, rate limiting y health
routers/                # Endpoints por dominio (chat, vision, rag, nlp, prompt_lab)
services/
  gemini_service.py     # Wrapper de Gemini (google-genai)
  rag_service.py        # Indexado y consulta RAG (LangChain + ChromaDB)
static/                 # SPA (HTML, CSS y JS)
data/                   # Documento de demo para el RAG
Procfile                # Comando de arranque (Railway)
```

## Autor

**Miguel Ángel Calzada Martín** — Software Developer · IA & Big Data

- GitHub: [@miguelcalzada-dev](https://github.com/miguelcalzada-dev)
- Web: [miguelcalzada.com](https://miguelcalzada.com)

## Licencia

Distribuido bajo licencia **MIT**. Consulta [LICENSE](./LICENSE) para más información.
