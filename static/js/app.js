/* app.js — Global state, tab routing, utilities */

// ── Marked.js CDN config (loaded in index.html) ──
let markedReady = false;
document.addEventListener('DOMContentLoaded', () => {
  if (typeof marked !== 'undefined') {
    marked.setOptions({ breaks: true, gfm: true });
    markedReady = true;
  }
});

// ── Tab Router ──
document.addEventListener('DOMContentLoaded', () => {
  const tabBtns  = document.querySelectorAll('.tab-btn');
  const panels   = document.querySelectorAll('.tab-panel');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const tabNavInner = document.getElementById('tab-nav-inner');

  if (mobileMenuBtn && tabNavInner) {
    mobileMenuBtn.addEventListener('click', () => {
      tabNavInner.classList.toggle('open');
      const isOpen = tabNavInner.classList.contains('open');
      mobileMenuBtn.innerHTML = isOpen ? 'Cerrar ✕' : 'Menú ☰';
    });
  }

  function activateTab(tabId) {
    tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
    panels.forEach(p => p.classList.toggle('active', p.id === 'panel-' + tabId));
    localStorage.setItem('ai-demo-tab', tabId);
    
    // Auto-close menu on mobile after selection
    if (tabNavInner && tabNavInner.classList.contains('open')) {
      tabNavInner.classList.remove('open');
      if (mobileMenuBtn) mobileMenuBtn.innerHTML = 'Menú ☰';
    }
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.dataset.tab));
  });

  // Restore last tab
  const saved = localStorage.getItem('ai-demo-tab') || 'chat';
  activateTab(saved);

  // Init all modules (defined in their own files)
  if (typeof initChat      === 'function') initChat();
  if (typeof initVision    === 'function') initVision();
  if (typeof initRag       === 'function') initRag();
  if (typeof initPromptLab === 'function') initPromptLab();
  if (typeof initNlp       === 'function') initNlp();
  if (typeof initVoice     === 'function') initVoice();
});

// ── Toast Notifications ──
const toastContainer = (() => {
  const el = document.createElement('div');
  el.className = 'toast-container';
  document.body.appendChild(el);
  return el;
})();

function showToast(message, type = 'info', icon = null) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-icon">${icon || icons[type]}</span><span>${message}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}

// ── Markdown Renderer ──
function renderMarkdown(text) {
  if (markedReady && typeof marked !== 'undefined') {
    try { return marked.parse(text); } catch (_) { }
  }
  // Fallback: basic escaping
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
}

// ── Spinner helpers ──
function setLoading(btn, loading, text = null) {
  if (!btn) return;
  btn.disabled = loading;
  if (loading) {
    btn._origHTML = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span>${text ? ' ' + text : ''}`;
  } else {
    btn.innerHTML = btn._origHTML || btn.innerHTML;
  }
}

// ── API fetch helper ──
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      let errMsg = `Error ${res.status}`;
      try { const e = await res.json(); errMsg = e.detail || errMsg; } catch (_) {}
      throw new Error(errMsg);
    }
    return await res.json();
  } catch (err) {
    throw err;
  }
}

// ── Textarea auto-resize ──
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 180) + 'px';
}

// ── Format JSON for display ──
function formatJSON(obj) {
  return JSON.stringify(obj, null, 2);
}

// ── Intersection Observer for Micro-interactions ──
document.addEventListener('DOMContentLoaded', () => {
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        // Unobserve after animating once
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Seleccionar tarjetas y elementos que queramos animar
  const animateElements = document.querySelectorAll('.card, .nlp-tool-card');
  animateElements.forEach(el => {
    // Inicialmente los bajamos un poco por CSS si no tienen .in-view
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out, box-shadow 0.15s ease-out';
    observer.observe(el);
  });
  
  // Agregar al CSS en caso de que app.js manipule el DOM
  const style = document.createElement('style');
  style.textContent = `
    .card.in-view, .nlp-tool-card.in-view {
      opacity: 1 !important;
      transform: translateY(0) !important;
    }
    .card.in-view:hover {
      transform: translate(-2px, -2px) !important;
    }
  `;
  document.head.appendChild(style);
});
