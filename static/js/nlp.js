/* nlp.js — Herramientas NLP: Sentimiento, Resumen, Clasificación */

function initNlp() {
  document.getElementById('nlp-sentiment-btn')?.addEventListener('click', analyzeSentiment);
  document.getElementById('nlp-summarize-btn')?.addEventListener('click', summarizeText);
  document.getElementById('nlp-classify-btn')?.addEventListener('click',  classifyText);
}

// ── Sentiment Analysis ──
async function analyzeSentiment() {
  const input   = document.getElementById('nlp-sentiment-input');
  const result  = document.getElementById('nlp-sentiment-result');
  const btn     = document.getElementById('nlp-sentiment-btn');
  const text    = input?.value?.trim();

  if (!text) { showToast('Introduce un texto para analizar', 'warning'); return; }

  setLoading(btn, true, 'Analizando…');
  result.innerHTML = '<div class="skeleton" style="height:90px"></div>';

  try {
    const data = await apiFetch('/api/nlp/sentiment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });

    if (data.raw) {
      result.innerHTML = `<div class="json-result">${escapeHtml(data.raw)}</div>`;
      return;
    }

    const sentiment = (data.sentiment || 'neutro').toLowerCase();
    const score     = typeof data.score === 'number' ? data.score : 0;
    // Normalize score to 0-100% bar (score is -1 to 1)
    const pct = Math.round(((score + 1) / 2) * 100);

    const emotions = (data.emotions || []).map(e => `<span class="tag">${e}</span>`).join('');
    const keywords = (data.keywords || []).map(k => `<span class="tag">${k}</span>`).join('');
    const conf     = data.confidence !== undefined ? Math.round(data.confidence * 100) : null;

    result.innerHTML = `
      <div class="sentiment-pill sentiment-${sentiment}">
        ${sentimentEmoji(sentiment)} ${capitalize(sentiment)}
        ${conf !== null ? `<span style="opacity:.7;font-size:.75em">(${conf}%)</span>` : ''}
      </div>
      <div class="score-bar-wrap">
        <div style="display:flex;justify-content:space-between;font-size:.75rem;color:var(--text-dim);margin-bottom:4px">
          <span>Muy negativo</span><span>Muy positivo</span>
        </div>
        <div class="score-bar-track">
          <div class="score-bar-fill" style="width:${pct}%"></div>
        </div>
        <div style="text-align:center;font-size:.75rem;color:var(--text-muted);margin-top:4px">Score: ${score.toFixed(2)}</div>
      </div>
      ${emotions ? `<div class="tag-list">${emotions}</div>` : ''}
      ${keywords ? `<div class="tag-list" style="margin-top:6px">${keywords}</div>` : ''}
      ${data.explanation ? `<p class="text-sm" style="margin-top:10px">${data.explanation}</p>` : ''}`;
  } catch (err) {
    result.textContent = '⚠️ ' + err.message;
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Summarize ──
async function summarizeText() {
  const input   = document.getElementById('nlp-summarize-input');
  const result  = document.getElementById('nlp-summarize-result');
  const btn     = document.getElementById('nlp-summarize-btn');
  const wordsEl = document.getElementById('nlp-summarize-words');
  const text    = input?.value?.trim();

  if (!text) { showToast('Introduce un texto para resumir', 'warning'); return; }

  setLoading(btn, true, 'Resumiendo…');
  result.innerHTML = '<div class="skeleton" style="height:80px"></div>';

  try {
    const data = await apiFetch('/api/nlp/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, max_words: parseInt(wordsEl?.value || '80') }),
    });
    result.innerHTML = `
      <p style="line-height:1.7">${escapeHtml(data.summary)}</p>
      <p class="text-xs" style="margin-top:10px">📊 ${data.words} palabras</p>`;
  } catch (err) {
    result.textContent = '⚠️ ' + err.message;
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Classify Intent ──
async function classifyText() {
  const input  = document.getElementById('nlp-classify-input');
  const result = document.getElementById('nlp-classify-result');
  const btn    = document.getElementById('nlp-classify-btn');
  const text   = input?.value?.trim();

  if (!text) { showToast('Introduce un texto para clasificar', 'warning'); return; }

  setLoading(btn, true, 'Clasificando…');
  result.innerHTML = '<div class="skeleton" style="height:120px"></div>';

  try {
    const data = await apiFetch('/api/nlp/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });

    if (data.raw) {
      result.innerHTML = `<div class="json-result">${escapeHtml(data.raw)}</div>`;
      return;
    }

    const conf = data.confidence !== undefined ? Math.round(data.confidence * 100) : null;
    result.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
        ${classifyRow('🎯 Intención',  capitalize(data.intent  || '—'))}
        ${classifyRow('📂 Categoría',  capitalize(data.category || '—'))}
        ${classifyRow('🌐 Idioma',     capitalize(data.language || '—'))}
        ${classifyRow('🎭 Tono',       capitalize(data.tone     || '—'))}
        ${classifyRow('❓ Es pregunta', data.is_question ? 'Sí' : 'No')}
        ${classifyRow('🔍 Subjetividad', capitalize(data.subjectivity || '—'))}
      </div>
      ${conf !== null ? `<div class="score-bar-wrap"><div class="score-bar-track"><div class="score-bar-fill" style="width:${conf}%"></div></div><div class="text-xs" style="margin-top:4px">Confianza: ${conf}%</div></div>` : ''}
      ${data.explanation ? `<p class="text-sm" style="margin-top:10px">${data.explanation}</p>` : ''}`;
  } catch (err) {
    result.textContent = '⚠️ ' + err.message;
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Helpers ──
function sentimentEmoji(s) {
  return { positivo: '😊', negativo: '😞', neutro: '😐', mixto: '😕' }[s] || '🔍';
}
function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }
function escapeHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function classifyRow(label, value) {
  return `<div style="background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:var(--radius);padding:8px 10px">
    <div class="text-xs" style="margin-bottom:3px">${label}</div>
    <div style="font-size:.85rem;font-weight:600">${escapeHtml(value)}</div>
  </div>`;
}
