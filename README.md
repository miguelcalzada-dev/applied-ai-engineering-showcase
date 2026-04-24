# Applied AI Engineering Showcase

Esta es una **Aplicación Web Interactiva** diseñada para mostrar múltiples capacidades como desarrollador de Inteligencia Artificial ("AI Engineer"). Está construida sobre una arquitectura **FastAPI (Python)** para el backend y una interfaz **Brutalista y Editorial (Vanilla JS/CSS)** en el frontend.

El proyecto consolida los casos de uso más demandados en la industria de la IA (LLMs, RAG, Visión por Computadora y Procesamiento de Lenguaje Natural) en una suite unificada y lista para auditar.

---

## 🌐 Demo en Vivo

La aplicación se encuentra desplegada y funcionando en producción a través de Railway:
👉 **[https://web-production-2ec10.up.railway.app/](https://web-production-2ec10.up.railway.app/)**

---

## 🌟 Características y Módulos

1. **💬 Chat Multi-turno (LLM Core)**
   - Conversaciones con memoria de contexto persistente.
   - Parámetros ajustables: *System Prompt* y *Temperatura*.
   - Transcripción y envío de voz (MediaRecorder API).

2. **👁️ Análisis de Imágenes (Vision)**
   - Subida de imágenes vía "Drag & Drop".
   - Captura directa desde la **Webcam** usando JS + HTML5.
   - Análisis avanzado y descripción mediante Gemini Vision.

3. **📚 RAG (Retrieval-Augmented Generation)**
   - Carga de documentos `.txt` o `.pdf` en tiempo real.
   - Vectorización y búsqueda de fragmentos con **LangChain**, **HuggingFace Embeddings** y **ChromaDB**.
   - Generación de respuestas basadas 100% en el contexto del documento con acordeón para auditar los fragmentos recuperados.

4. **🔬 Laboratorio de Prompts (Prompt Engineering)**
   - Zona de testeo puro para roles y configuraciones avanzadas.
   - Visualización de métricas de ejecución: **Latencia, estimación de tokens (entrada/salida)** y recuento de palabras.

5. **📊 NLP Tools (Procesamiento de Lenguaje Natural)**
   - **Análisis de sentimiento**: barra visual de *score*, emociones y palabras clave.
   - **Resumen texto**: compresión al tamaño en palabras deseado.
   - **Clasificador de intención**: categorización temática, detección de formato (pregunta/información) e idioma.

6. **🎙️ Asistente de Voz (Speech-to-Text & Text-to-Speech)**
   - Una interfaz "Manos libres" que graba tu voz y responde hablando.
   - Utiliza la API de MediaRecorder junto a las capacidades de audio nativo de Gemini para lograr máxima compatibilidad en móviles y escritorio.

---

## 🛠️ Stack Tecnológico

- **Backend**: FastAPI, Pydantic, Python-multipart (para subida de archivos).
- **IA & Modelos**: API de Google Gemini (`gemini-2.5-flash` y vision).
- **RAG Stack**: LangChain, ChromaDB, Huggingface `sentence-transformers`.
- **Frontend**: Single Page Application en Vanilla JavaScript y CSS (Glassmorphism + Modo Oscuro).

---

## 🚀 Instalación y Ejecución local

Asegúrate de tener Python 3.9 o superior instalado.

1. **Clonar este repositorio o acceder a la carpeta**:
   ```bash
   cd ai-portfolio-demo
   ```

2. **Crear y activar un Entorno Virtual** *(recomendado)*:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac / Linux
   # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variables de Entorno**:
   - Copia el archivo `.env.example` y renómbralo a `.env`.
   - Edítalo y añade tu clave de la API de Google Gemini. *(Si no tienes una, consíguela en [Google AI Studio](https://aistudio.google.com/))*
   ```bash
   cp .env.example .env
   # Edita el archivo .env -> GEMINI_API_KEY=tu_api_key_aqui
   ```

5. **Lanzar el Servidor**:
   ```bash
   uvicorn main:app --reload
   ```

6. **Abrir la aplicación**:
   - Ve a tu navegador: `http://localhost:8000`
   - Si quieres ver la documentación automática de la API: `http://localhost:8000/docs`
