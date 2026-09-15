/* chat.js — Chat multi-turno con Gemini */

let chatSessionId  = null;
let chatIsWaiting  = false;

function initChat() {
  const input      = document.getElementById('chat-input');
  const sendBtn    = document.getElementById('chat-send');
  const clearBtn   = document.getElementById('chat-clear');
  const voiceBtn   = document.getElementById('chat-voice-btn');
  const tempSlider = document.getElementById('chat-temp');
  const tempVal    = document.getElementById('chat-temp-val');
  const systemIn   = document.getElementById('chat-system');

  if (!input) return;

  // Temperature slider display
  if (tempSlider) {
    tempSlider.addEventListener('input', () => {
      tempVal.textContent = parseFloat(tempSlider.value).toFixed(1);
    });
  }

  // Auto-resize textarea
  input.addEventListener('input', () => autoResize(input));

  // Send on Enter (Shift+Enter = newline)
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  if (sendBtn)  sendBtn.addEventListener('click', sendChatMessage);
  if (clearBtn) clearBtn.addEventListener('click', clearChat);

  // Voice input for chat (Web Speech API)
  if (voiceBtn) {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      voiceBtn.style.display = 'none';
    } else {
      voiceBtn.addEventListener('click', () => startChatVoiceInput(input));
    }
  }
}

function startChatVoiceInput(input) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.lang = 'es-ES';
  recognition.interimResults = false;

  recognition.onstart = () => {
    document.getElementById('chat-voice-btn').textContent = '🔴';
    showToast('Escuchando…', 'info', '🎙️');
  };
  recognition.onresult = e => {
    input.value = e.results[0][0].transcript;
    autoResize(input);
    document.getElementById('chat-voice-btn').textContent = '🎙️';
  };
  recognition.onerror = () => {
    document.getElementById('chat-voice-btn').textContent = '🎙️';
    showToast('No se pudo acceder al micrófono', 'error');
  };
  recognition.onend = () => {
    document.getElementById('chat-voice-btn').textContent = '🎙️';
  };
  recognition.start();
}

async function sendChatMessage() {
  if (chatIsWaiting) return;
  const input    = document.getElementById('chat-input');
  const sendBtn  = document.getElementById('chat-send');
  const tempSlider = document.getElementById('chat-temp');
  const systemIn = document.getElementById('chat-system');
  const text     = input.value.trim();
  if (!text) return;

  chatIsWaiting = true;
  appendChatMessage('user', text);
  input.value = '';
  autoResize(input);
  setLoading(sendBtn, true);

  // Loading bubble
  const loadingBubble = appendLoadingBubble();

  try {
    const data = await apiFetch('api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: chatSessionId,
        message: text,
        system_prompt: systemIn ? systemIn.value.trim() : '',
        temperature: tempSlider ? parseFloat(tempSlider.value) : 0.7,
      }),
    });
    chatSessionId = data.session_id;
    loadingBubble.remove();
    appendChatMessage('assistant', data.response);
  } catch (err) {
    loadingBubble.remove();
    appendChatMessage('assistant', `⚠️ **Error:** ${err.message}`);
    showToast(err.message, 'error');
  } finally {
    chatIsWaiting = false;
    setLoading(sendBtn, false);
  }
}

function appendChatMessage(role, content) {
  const messages = document.getElementById('chat-messages');
  const empty    = document.getElementById('chat-empty');
  if (empty) empty.style.display = 'none';

  const wrap = document.createElement('div');
  wrap.className = `message ${role === 'user' ? 'user' : 'assistant'}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '👤' : '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = renderMarkdown(content);

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

function appendLoadingBubble() {
  const messages = document.getElementById('chat-messages');
  const wrap = document.createElement('div');
  wrap.className = 'message assistant';
  wrap.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-loading">
      <div class="dot-flashing"></div>
      <div class="dot-flashing"></div>
      <div class="dot-flashing"></div>
    </div>`;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

async function clearChat() {
  if (chatSessionId) {
    try { await apiFetch(`api/chat/${chatSessionId}`, { method: 'DELETE' }); } catch (_) {}
    chatSessionId = null;
  }
  const messages = document.getElementById('chat-messages');
  messages.innerHTML = `
    <div class="chat-empty" id="chat-empty">
      <div class="chat-empty-icon">💬</div>
      <div class="chat-empty-text">Escribe un mensaje para empezar la conversación</div>
    </div>`;
  showToast('Conversación limpiada', 'success');
}
