/* vision.js — Análisis de imágenes con Gemini Vision (upload + webcam) */

let visionStream    = null;
let visionBlob      = null;
let visionSourceMode = 'upload'; // 'upload' | 'camera'

function initVision() {
  const uploadTab  = document.getElementById('vision-tab-upload');
  const cameraTab  = document.getElementById('vision-tab-camera');
  const dropZone   = document.getElementById('vision-drop-zone');
  const fileInput  = document.getElementById('vision-file-input');
  const startCamBtn= document.getElementById('vision-start-cam');
  const captureBtn = document.getElementById('vision-capture');
  const analyzeBtn = document.getElementById('vision-analyze');
  const clearBtn   = document.getElementById('vision-clear');
  const video      = document.getElementById('vision-video');

  if (!analyzeBtn) return;

  // Source tabs
  uploadTab?.addEventListener('click', () => switchVisionSource('upload'));
  cameraTab?.addEventListener('click', () => switchVisionSource('camera'));

  // File drop zone
  dropZone?.addEventListener('click', () => fileInput?.click());
  dropZone?.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone?.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelected(file);
  });
  fileInput?.addEventListener('change', () => {
    if (fileInput.files[0]) handleFileSelected(fileInput.files[0]);
  });

  // Camera
  startCamBtn?.addEventListener('click', startCamera);
  captureBtn?.addEventListener('click',  capturePhoto);

  // Analyze & clear
  analyzeBtn.addEventListener('click', analyzeImage);
  clearBtn?.addEventListener('click',   clearVision);
}

function switchVisionSource(mode) {
  visionSourceMode = mode;
  document.getElementById('vision-tab-upload')?.classList.toggle('active', mode === 'upload');
  document.getElementById('vision-tab-camera')?.classList.toggle('active', mode === 'camera');
  document.getElementById('vision-source-upload')?.classList.toggle('active', mode === 'upload');
  document.getElementById('vision-source-camera')?.classList.toggle('active', mode === 'camera');

  if (mode === 'upload' && visionStream) stopCamera();
}

function handleFileSelected(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Por favor, selecciona un archivo de imagen', 'error');
    return;
  }
  visionBlob = file;
  const reader = new FileReader();
  reader.onload = e => showImagePreview(e.target.result);
  reader.readAsDataURL(file);
}

async function startCamera() {
  const overlay = document.getElementById('vision-cam-overlay');
  const captureBtn = document.getElementById('vision-capture');
  const video  = document.getElementById('vision-video');
  try {
    visionStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
    video.srcObject = visionStream;
    video.play();
    if (overlay) overlay.style.display = 'none';
    if (captureBtn) captureBtn.disabled = false;
    document.getElementById('vision-start-cam').style.display = 'none';
  } catch (err) {
    showToast('No se pudo acceder a la cámara: ' + err.message, 'error');
  }
}

function stopCamera() {
  visionStream?.getTracks().forEach(t => t.stop());
  visionStream = null;
}

function capturePhoto() {
  const video  = document.getElementById('vision-video');
  if (!video || !visionStream) return;
  const canvas = document.createElement('canvas');
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  canvas.toBlob(blob => {
    visionBlob = blob;
    showImagePreview(canvas.toDataURL('image/jpeg'));
    showToast('Foto capturada', 'success', '📷');
  }, 'image/jpeg', 0.92);
}

function showImagePreview(src) {
  const preview = document.getElementById('vision-preview');
  const empty   = document.getElementById('vision-preview-empty');
  if (!preview) return;
  preview.innerHTML = `<img src="${src}" alt="Imagen seleccionada" />`;
  if (empty) empty.style.display = 'none';
}

async function analyzeImage() {
  if (!visionBlob) {
    showToast('Selecciona o captura una imagen primero', 'warning');
    return;
  }
  const question  = document.getElementById('vision-question')?.value?.trim()
    || '¿Qué ves en esta imagen? Descríbelo en detalle.';
  const btn       = document.getElementById('vision-analyze');
  const resultEl  = document.getElementById('vision-result');

  setLoading(btn, true, 'Analizando...');
  resultEl.textContent = '';

  const formData = new FormData();
  formData.append('image', visionBlob, 'capture.jpg');
  formData.append('question', question);

  try {
    const data = await apiFetch('api/vision', { method: 'POST', body: formData });
    resultEl.textContent = data.result;
    resultEl.classList.add('has-content');
  } catch (err) {
    resultEl.textContent = '⚠️ Error: ' + err.message;
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

function clearVision() {
  visionBlob = null;
  const preview = document.getElementById('vision-preview');
  if (preview) preview.innerHTML = `<div class="image-preview-empty" id="vision-preview-empty">📸 La imagen aparecerá aquí</div>`;
  const result = document.getElementById('vision-result');
  if (result) { result.textContent = 'El análisis aparecerá aquí…'; result.classList.remove('has-content'); }
  const fileInput = document.getElementById('vision-file-input');
  if (fileInput) fileInput.value = '';
}
