/* voice.js — Asistente de Voz (Web Speech API + Gemini) */

let voiceSessionId  = null;
let recognition     = null;
let isListening     = false;
let isSpeaking      = false;

function initVoice() {
  const micBtn   = document.getElementById('voice-mic-btn');
  const stopBtn  = document.getElementById('voice-stop-btn');
  const clearBtn = document.getElementById('voice-clear-btn');
  const langSel  = document.getElementById('voice-lang');

  if (!micBtn) return;

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    document.getElementById('voice-not-supported')?.classList.remove('hidden');
    micBtn.disabled = true;
    return;
  }

  recognition = new SpeechRec();
  recognition.interimResults = true;
  recognition.continuous     = false;

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    micBtn.querySelector('.mic-rings')?.classList.add('listening');// rings on parent
    setVoiceStatus('listening', '🎙️ Escuchando…');
    if (stopBtn) stopBtn.disabled = false;
  };

  recognition.onresult = e => {
    let interim = '', final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript;
      else interim += e.results[i][0].transcript;
    }
    const transcriptEl = document.getElementById('voice-transcript');
    if (transcriptEl) {
      transcriptEl.textContent = final || interim;
      transcriptEl.classList.toggle('has-text', !!(final || interim));
    }
    if (final) onFinalTranscript(final);
  };

  recognition.onerror = e => {
    setVoiceStatus('', `❌ Error: ${e.error}`);
    stopListening();
    showToast('Error de reconocimiento: ' + e.error, 'error');
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove('listening');
    setWrapListeningClass(false);
    if (stopBtn) stopBtn.disabled = true;
  };

  micBtn.addEventListener('click', toggleListening);
  stopBtn?.addEventListener('click', stopListening);
  clearBtn?.addEventListener('click', clearVoice);
  langSel?.addEventListener('change', () => {
    if (recognition) recognition.lang = langSel.value;
  });

  // Set initial language
  if (langSel) recognition.lang = langSel.value;
}

function setWrapListeningClass(on) {
  const wrap = document.getElementById('voice-mic-wrap');
  if (wrap) wrap.classList.toggle('listening', on);
}

function toggleListening() {
  if (isListening) stopListening();
  else startListening();
}

function startListening() {
  if (!recognition || isListening || isSpeaking) return;
  const langSel = document.getElementById('voice-lang');
  if (langSel) recognition.lang = langSel.value;

  const transcriptEl = document.getElementById('voice-transcript');
  if (transcriptEl) { transcriptEl.textContent = ''; transcriptEl.classList.remove('has-text'); }

  try { recognition.start(); setWrapListeningClass(true); }
  catch (e) { showToast('No se pudo iniciar el micrófono', 'error'); }
}

function stopListening() {
  if (recognition && isListening) recognition.stop();
  isListening = false;
  document.getElementById('voice-mic-btn')?.classList.remove('listening');
  setWrapListeningClass(false);
  setVoiceStatus('', '🎙️ Pulsa el micrófono para hablar');
}

async function onFinalTranscript(text) {
  setVoiceStatus('processing', '⚙️ Procesando respuesta…');
  const responseEl = document.getElementById('voice-response');
  if (responseEl) { responseEl.textContent = '…'; responseEl.classList.remove('has-text'); }

  try {
    const data = await apiFetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: voiceSessionId,
        message: text,
        system_prompt: 'Responde de forma breve, natural y conversacional. Máximo 3 frases.',
        temperature: 0.75,
      }),
    });
    voiceSessionId = data.session_id;

    if (responseEl) {
      responseEl.textContent = data.response;
      responseEl.classList.add('has-text');
    }

    speakResponse(data.response);
  } catch (err) {
    setVoiceStatus('', '❌ Error al obtener respuesta');
    showToast(err.message, 'error');
  }
}

function speakResponse(text) {
  if (!window.speechSynthesis) return;

  const langSel = document.getElementById('voice-lang');
  const lang    = langSel ? langSel.value : 'es-ES';

  window.speechSynthesis.cancel();
  isSpeaking = true;
  setVoiceStatus('speaking', '🔊 Hablando…');

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang  = lang;
  utterance.rate  = 1.0;
  utterance.pitch = 1.0;

  // Prefer a natural voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith(lang.split('-')[0]) && !v.name.includes('Google'))
    || voices.find(v => v.lang.startsWith(lang.split('-')[0]));
  if (preferred) utterance.voice = preferred;

  utterance.onend = () => {
    isSpeaking = false;
    setVoiceStatus('', '🎙️ Pulsa el micrófono para hablar');
  };
  utterance.onerror = () => {
    isSpeaking = false;
    setVoiceStatus('', '🎙️ Pulsa el micrófono para hablar');
  };

  window.speechSynthesis.speak(utterance);
}

function setVoiceStatus(type, text) {
  const el = document.getElementById('voice-status');
  if (!el) return;
  el.className = `voice-status${type ? ' ' + type : ''}`;
  el.textContent = text;
}

function clearVoice() {
  window.speechSynthesis?.cancel();
  if (isListening) stopListening();
  voiceSessionId = null;
  isSpeaking = false;

  const transcriptEl = document.getElementById('voice-transcript');
  const responseEl   = document.getElementById('voice-response');
  if (transcriptEl) { transcriptEl.textContent = ''; transcriptEl.classList.remove('has-text'); }
  if (responseEl)   { responseEl.textContent   = ''; responseEl.classList.remove('has-text'); }

  setVoiceStatus('', '🎙️ Pulsa el micrófono para hablar');
  showToast('Sesión de voz limpiada', 'success');
}
