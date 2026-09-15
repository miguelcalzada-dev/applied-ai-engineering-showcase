/* voice.js — Asistente de Voz (MediaRecorder + Gemini Audio) */

let voiceSessionId  = null;
let mediaRecorder   = null;
let audioChunks     = [];
let isListening     = false;
let isSpeaking      = false;

function initVoice() {
  const micBtn   = document.getElementById('voice-mic-btn');
  const stopBtn  = document.getElementById('voice-stop-btn');
  const clearBtn = document.getElementById('voice-clear-btn');
  const langSel  = document.getElementById('voice-lang');

  if (!micBtn) return;

  micBtn.addEventListener('click', toggleListening);
  stopBtn?.addEventListener('click', stopListening);
  clearBtn?.addEventListener('click', clearVoice);
  
  // Verificamos soporte de micrófono
  const notSupported = document.getElementById('voice-not-supported');
  if (notSupported) {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          notSupported.classList.remove('hidden');
          notSupported.innerHTML = '<p>⚠️ Tu navegador no soporta el acceso al micrófono. Requiere HTTPS o localhost.</p>';
          micBtn.disabled = true;
      } else {
          notSupported.classList.add('hidden');
      }
  }
}

function setWrapListeningClass(on) {
  const wrap = document.getElementById('voice-mic-wrap');
  if (wrap) wrap.classList.toggle('listening', on);
}

async function toggleListening() {
  if (isListening) stopListening();
  else await startListening();
}

async function startListening() {
  if (isListening || isSpeaking) return;

  const transcriptEl = document.getElementById('voice-transcript');
  if (transcriptEl) { transcriptEl.textContent = '🎙️ Grabando... (Pulsa de nuevo para enviar)'; transcriptEl.classList.add('has-text'); }
  const responseEl = document.getElementById('voice-response');
  if (responseEl) { responseEl.textContent = ''; responseEl.classList.remove('has-text'); }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstart = () => {
      isListening = true;
      const micBtn = document.getElementById('voice-mic-btn');
      if (micBtn) {
          micBtn.classList.add('listening');
          micBtn.querySelector('.mic-rings')?.classList.add('listening');
      }
      setWrapListeningClass(true);
      setVoiceStatus('listening', '🎙️ Grabando… (Pulsa para detener y enviar)');
      const stopBtn = document.getElementById('voice-stop-btn');
      if (stopBtn) stopBtn.disabled = false;
    };

    mediaRecorder.onstop = async () => {
      isListening = false;
      const micBtn = document.getElementById('voice-mic-btn');
      if (micBtn) {
          micBtn.classList.remove('listening');
          micBtn.querySelector('.mic-rings')?.classList.remove('listening');
      }
      setWrapListeningClass(false);
      const stopBtn = document.getElementById('voice-stop-btn');
      if (stopBtn) stopBtn.disabled = true;

      // Detener micrófono
      stream.getTracks().forEach(track => track.stop());

      // Enviar audio al backend
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      await sendAudioToBackend(audioBlob);
    };

    mediaRecorder.start();
  } catch (err) {
    console.error(err);
    showToast('No se pudo acceder al micrófono. Verifica permisos o usa HTTPS.', 'error');
    setVoiceStatus('', '❌ Error de micrófono');
  }
}

function stopListening() {
  if (mediaRecorder && isListening) {
    mediaRecorder.stop();
  }
}

async function sendAudioToBackend(audioBlob) {
  setVoiceStatus('processing', '⚙️ Procesando audio con Gemini...');
  const transcriptEl = document.getElementById('voice-transcript');
  if (transcriptEl) { transcriptEl.textContent = '...'; transcriptEl.classList.add('has-text'); }
  const responseEl = document.getElementById('voice-response');
  if (responseEl) { responseEl.textContent = '...'; responseEl.classList.remove('has-text'); }

  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.webm');
    if (voiceSessionId) formData.append('session_id', voiceSessionId);
    
    // Configuración para que el asistente sea conciso
    formData.append('system_prompt', 'Responde de forma breve, natural y conversacional. Máximo 3 frases.');
    formData.append('temperature', '0.75');

    const res = await fetch('api/chat/voice', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
        throw new Error('Error al enviar audio al servidor. ¿Problema de red o servidor caído?');
    }

    const data = await res.json();
    voiceSessionId = data.session_id;

    if (transcriptEl) {
        transcriptEl.textContent = data.transcript || '(Ininteligible)';
    }

    if (responseEl) {
      responseEl.textContent = data.response || '(Sin respuesta)';
      responseEl.classList.add('has-text');
    }

    speakResponse(data.response);
  } catch (err) {
    setVoiceStatus('', '❌ Error al procesar audio');
    showToast(err.message, 'error');
    if (transcriptEl) transcriptEl.textContent = 'Error de comunicación.';
  }
}

function speakResponse(text) {
  if (!window.speechSynthesis || !text) return;

  const langSel = document.getElementById('voice-lang');
  const lang    = langSel ? langSel.value : 'es-ES';

  window.speechSynthesis.cancel();
  isSpeaking = true;
  setVoiceStatus('speaking', '🔊 Hablando…');

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang  = lang;
  utterance.rate  = 1.0;
  utterance.pitch = 1.0;

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
