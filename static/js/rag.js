/* rag.js — RAG Chatbot con documentos */

let ragSessionId  = null;
let ragIsWaiting  = false;

function initRag() {
  const uploadBtn  = document.getElementById('rag-upload-btn');
  const fileInput  = document.getElementById('rag-file-input');
  const demoBtn    = document.getElementById('rag-demo-btn');
  const sendBtn    = document.getElementById('rag-send');
  const clearBtn   = document.getElementById('rag-clear');
  const input      = document.getElementById('rag-input');

  if (!sendBtn) return;

  fileInput?.addEventListener('change', () => {
    if (fileInput.files[0]) uploadDocument(fileInput.files[0]);
  });
  uploadBtn?.addEventListener('click', () => fileInput?.click());
  demoBtn?.addEventListener('click', loadDemoDocument);
  sendBtn.addEventListener('click', sendRagMessage);
  clearBtn?.addEventListener('click', clearRagChat);

  input?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendRagMessage(); }
  });
  input?.addEventListener('input', () => autoResize(input));
}

async function uploadDocument(file) {
  const btn = document.getElementById('rag-upload-btn');
  setLoading(btn, true, 'Indexando…');
  setRagStatus('loading', '⏳ Indexando documento…');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const data = await apiFetch('/api/rag/upload', { method: 'POST', body: formData });
    ragSessionId = data.session_id;
    setRagStatus('ready', `✅ "${file.name}" indexado (${data.words.toLocaleString()} palabras)`);
    document.getElementById('rag-send').disabled = false;
    document.getElementById('rag-input').disabled = false;
    showToast('Documento listo. ¡Empieza a preguntar!', 'success');
    appendRagMessage('assistant',
      `📄 He indexado **${file.name}** (${data.words.toLocaleString()} palabras, ${data.chars.toLocaleString()} caracteres).\n\nPuedes hacerme preguntas sobre su contenido y responderé basándome exclusivamente en él.`
    );
    clearRagMessages(false);
  } catch (err) {
    setRagStatus('idle', '❌ Error al subir el documento');
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

async function loadDemoDocument() {
  const btn = document.getElementById('rag-demo-btn');
  setLoading(btn, true, 'Cargando…');
  setRagStatus('loading', '⏳ Cargando documento de demo…');

  try {
    const data = await apiFetch('/api/rag/demo');
    ragSessionId = data.session_id;
    setRagStatus('ready', '✅ Demo: Guía de Tecnologías de IA cargada');
    document.getElementById('rag-send').disabled  = false;
    document.getElementById('rag-input').disabled = false;
    clearRagMessages(false);
    appendRagMessage('assistant',
      `📚 He cargado la **Guía de Tecnologías de IA** como documento de demo.\n\nContiene información sobre LLMs, RAG, Embeddings, NLP, Visión por Computador, Prompt Engineering y más.\n\nEjemplos de preguntas:\n- ¿Qué es RAG y cuáles son sus ventajas?\n- ¿Qué modelos de embeddings recomiendas?\n- ¿Cuál es la diferencia entre BERT y GPT?`
    );
    showToast('Documento demo cargado', 'success');
  } catch (err) {
    setRagStatus('idle', '❌ Error al cargar el demo');
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

async function sendRagMessage() {
  if (ragIsWaiting || !ragSessionId) return;
  const input   = document.getElementById('rag-input');
  const sendBtn = document.getElementById('rag-send');
  const text    = input.value.trim();
  if (!text) return;

  ragIsWaiting = true;
  appendRagMessage('user', text);
  input.value = '';
  autoResize(input);
  setLoading(sendBtn, true);

  const loader = appendRagLoader();
  try {
    const data = await apiFetch('/api/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: ragSessionId, question: text }),
    });
    loader.remove();
    appendRagMessage('assistant', data.response, data.context_used);
  } catch (err) {
    loader.remove();
    appendRagMessage('assistant', `⚠️ **Error:** ${err.message}`);
    showToast(err.message, 'error');
  } finally {
    ragIsWaiting = false;
    setLoading(sendBtn, false);
  }
}

function appendRagMessage(role, content, context = null) {
  const messages = document.getElementById('rag-messages');
  const empty    = document.getElementById('rag-empty');
  if (empty) empty.style.display = 'none';

  const wrap = document.createElement('div');
  wrap.className = `message ${role === 'user' ? 'user' : 'assistant'}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '👤' : '📚';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = renderMarkdown(content);

  // Context accordion
  if (context && role === 'assistant') {
    const accordion = document.createElement('div');
    accordion.className = 'context-accordion';
    accordion.innerHTML = `
      <button class="context-toggle" onclick="this.nextElementSibling.classList.toggle('open');this.textContent=this.nextElementSibling.classList.contains('open')?'▲ Ocultar fragmentos recuperados':'▼ Ver fragmentos recuperados del documento'">
        ▼ Ver fragmentos recuperados del documento
      </button>
      <div class="context-body">${context.replace(/</g,'&lt;')}</div>`;
    bubble.appendChild(accordion);
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

function appendRagLoader() {
  const messages = document.getElementById('rag-messages');
  const wrap = document.createElement('div');
  wrap.className = 'message assistant';
  wrap.innerHTML = `<div class="msg-avatar">📚</div><div class="msg-loading"><div class="dot-flashing"></div><div class="dot-flashing"></div><div class="dot-flashing"></div></div>`;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

function clearRagMessages(resetSession = true) {
  if (resetSession) {
    ragSessionId = null;
    setRagStatus('idle', 'Sin documento. Sube uno o usa el demo.');
    document.getElementById('rag-send').disabled  = true;
    document.getElementById('rag-input').disabled = true;
  }
  const messages = document.getElementById('rag-messages');
  if (messages) messages.innerHTML = `<div class="chat-empty" id="rag-empty"><div class="chat-empty-icon">📚</div><div class="chat-empty-text">Sube un documento para empezar</div></div>`;
}

function clearRagChat() { clearRagMessages(true); showToast('Chat RAG limpiado', 'success'); }

function setRagStatus(type, text) {
  const el = document.getElementById('rag-status');
  if (!el) return;
  el.className = `rag-status ${type}`;
  el.innerHTML = `<span class="rag-status-dot"></span>${text}`;
}
