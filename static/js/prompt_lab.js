/* prompt_lab.js — Laboratorio de Prompts con métricas */

function initPromptLab() {
  const runBtn  = document.getElementById('lab-run-btn');
  const clearBtn= document.getElementById('lab-clear-btn');
  const tempSlider = document.getElementById('lab-temp');
  const tempVal    = document.getElementById('lab-temp-val');
  const copyBtn    = document.getElementById('lab-copy-btn');

  if (!runBtn) return;

  tempSlider?.addEventListener('input', () => {
    if (tempVal) tempVal.textContent = parseFloat(tempSlider.value).toFixed(1);
    updateTempLabel(parseFloat(tempSlider.value));
  });

  runBtn.addEventListener('click', runPromptLab);
  clearBtn?.addEventListener('click', clearLab);
  copyBtn?.addEventListener('click', copyLabResponse);
}

function updateTempLabel(val) {
  const label = document.getElementById('lab-temp-desc');
  if (!label) return;
  if (val <= 0.2) label.textContent = 'Muy determinista';
  else if (val <= 0.4) label.textContent = 'Preciso';
  else if (val <= 0.6) label.textContent = 'Equilibrado';
  else if (val <= 0.8) label.textContent = 'Creativo';
  else label.textContent = 'Muy creativo';
}

async function runPromptLab() {
  const systemIn  = document.getElementById('lab-system');
  const userIn    = document.getElementById('lab-user');
  const tempEl    = document.getElementById('lab-temp');
  const responseEl= document.getElementById('lab-response');
  const runBtn    = document.getElementById('lab-run-btn');
  const copyBtn   = document.getElementById('lab-copy-btn');

  const userPrompt = userIn?.value?.trim();
  if (!userPrompt) { showToast('Escribe un prompt de usuario', 'warning'); return; }

  setLoading(runBtn, true, 'Ejecutando…');
  responseEl.classList.remove('has-content');
  responseEl.innerHTML = '<div class="dot-flashing" style="margin:auto"></div>';
  if (copyBtn) copyBtn.disabled = true;
  clearLabMetrics();

  const start = Date.now();
  try {
    const data = await apiFetch('/api/prompt-lab', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system_prompt: systemIn?.value?.trim() || '',
        user_prompt:   userPrompt,
        temperature:   tempEl ? parseFloat(tempEl.value) : 0.7,
      }),
    });

    const clientLatency = ((Date.now() - start) / 1000).toFixed(2);
    responseEl.innerHTML = renderMarkdown(data.response);
    responseEl.classList.add('has-content');
    if (copyBtn) copyBtn.disabled = false;

    const m = data.metrics || {};
    setMetric('metric-latency',   `${m.latency_seconds ?? clientLatency}s`);
    setMetric('metric-temp',      (m.temperature ?? 0.7).toFixed(1));
    setMetric('metric-in-tokens', m.estimated_input_tokens ?? '—');
    setMetric('metric-out-tokens',m.estimated_output_tokens ?? '—');
    setMetric('metric-words',     m.output_words ?? '—');
    setMetric('metric-sys',       m.has_system_prompt ? '✅ Sí' : '❌ No');

  } catch (err) {
    responseEl.textContent = '⚠️ ' + err.message;
    showToast(err.message, 'error');
  } finally {
    setLoading(runBtn, false);
  }
}

function setMetric(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function clearLabMetrics() {
  ['metric-latency','metric-temp','metric-in-tokens','metric-out-tokens','metric-words','metric-sys']
    .forEach(id => setMetric(id, '—'));
}

function clearLab() {
  document.getElementById('lab-system').value = '';
  document.getElementById('lab-user').value   = '';
  const responseEl = document.getElementById('lab-response');
  if (responseEl) { responseEl.innerHTML = ''; responseEl.classList.remove('has-content'); }
  clearLabMetrics();
  const copyBtn = document.getElementById('lab-copy-btn');
  if (copyBtn) copyBtn.disabled = true;
  showToast('Lab limpiado', 'success');
}

function copyLabResponse() {
  const responseEl = document.getElementById('lab-response');
  const text = responseEl?.textContent?.trim();
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => showToast('Respuesta copiada', 'success', '📋'));
}
