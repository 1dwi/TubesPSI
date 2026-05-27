/**
 * LeafSense AI - Frontend Logic
 * Drag & Drop, AJAX upload, result rendering, Live Camera
 * Features: Capture, History, Stats, Confidence Warning
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const btnRemove = document.getElementById('btnRemove');
    const btnPredict = document.getElementById('btnPredict');
    const btnNew = document.getElementById('btnNew');
    const resultsSection = document.getElementById('resultsSection');
    const uploadSectionContainer = document.getElementById('uploadSectionContainer');
    const errorToast = document.getElementById('errorToast');
    const errorMessage = document.getElementById('errorMessage');

    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Camera
    const cameraFeed = document.getElementById('cameraFeed');
    const cameraCanvas = document.getElementById('cameraCanvas');
    const detectionCanvas = document.getElementById('detectionCanvas');
    const detContext = detectionCanvas.getContext('2d');
    const cameraOverlay = document.getElementById('cameraOverlay');
    const btnStartCamera = document.getElementById('btnStartCamera');
    const liveIndicator = document.getElementById('liveIndicator');
    const btnCapture = document.getElementById('btnCapture');
    const btnSwitchCamera = document.getElementById('btnSwitchCamera');
    
    // Compare Elements
    const compareUploadLeft = document.getElementById('compareUploadLeft');
    const compareUploadRight = document.getElementById('compareUploadRight');
    const compareInputLeft = document.getElementById('compareInputLeft');
    const compareInputRight = document.getElementById('compareInputRight');
    const comparePreviewLeft = document.getElementById('comparePreviewLeft');
    const comparePreviewRight = document.getElementById('comparePreviewRight');
    const btnCompare = document.getElementById('btnCompare');
    const btnSlotRemoves = document.querySelectorAll('.btn-slot-remove');

    let selectedFile = null;
    let cameraStream = null;
    let scanInterval = null;
    let isScanning = false;
    let currentFacingMode = 'environment';
    let compareFiles = { left: null, right: null };

    // Bounding box smoothing state
    let currentBBox = null;
    let targetBBox = null;
    let lastBBoxLabel = '';
    let lastBBoxColor = '';
    let bboxAnimFrame = null;
    let bboxFadeTimeout = null;

    // Stats & History
    let stats = JSON.parse(localStorage.getItem('leafsense_stats') || '{"total":0,"daun muda":0,"daun menguning":0,"daun tua":0,"unknown":0,"captures":0}');
    // Ensure stats has all keys (backward compat)
    if (stats.muda !== undefined) {
        stats['daun muda'] = (stats['daun muda'] || 0) + stats.muda;
        delete stats.muda;
    }
    if (stats.sedang !== undefined) {
        stats['daun menguning'] = (stats['daun menguning'] || 0) + stats.sedang;
        delete stats.sedang;
    }
    if (stats.tua !== undefined) {
        stats['daun tua'] = (stats['daun tua'] || 0) + stats.tua;
        delete stats.tua;
    }
    if (!stats.unknown) stats.unknown = 0;
    if (!stats['daun menguning']) stats['daun menguning'] = 0;
    if (!stats['daun muda']) stats['daun muda'] = 0;
    if (!stats['daun tua']) stats['daun tua'] = 0;
    let history = JSON.parse(localStorage.getItem('leafsense_history') || '[]');
    let lastLiveData = null; // Store last live prediction for capture
    let statsChart = null; // Chart.js instance

    // --- Init ---
    createParticles();
    initChart();
    renderStats();
    renderHistory();

    // --- Background Particles ---
    function createParticles() {
        const container = document.getElementById('bgParticles');
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 15 + 's';
            particle.style.animationDuration = (10 + Math.random() * 10) + 's';
            particle.style.width = (2 + Math.random() * 4) + 'px';
            particle.style.height = particle.style.width;
            container.appendChild(particle);
        }
    }

    // --- Tabs Logic ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).style.display = 'block';
            if (targetId !== 'liveCameraTab') stopCamera();
        });
    });

    // --- Camera Logic ---
    async function startCamera() {
        if (cameraStream) stopCamera(false); // partial stop to preserve UI state if just switching

        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: currentFacingMode }
            });
            cameraFeed.srcObject = cameraStream;
            cameraOverlay.style.display = 'none';
            liveIndicator.style.display = 'flex';
            btnCapture.style.display = 'flex';
            btnSwitchCamera.style.display = 'flex';

            // Check if device has multiple cameras (only show switch button if multiple)
            navigator.mediaDevices.enumerateDevices().then(devices => {
                const videoInputs = devices.filter(device => device.kind === 'videoinput');
                if (videoInputs.length <= 1) {
                    btnSwitchCamera.style.display = 'none';
                }
            });

            isScanning = true;
            startScanning();
        } catch (err) {
            showError('Akses kamera ditolak atau kamera tidak ditemukan.');
        }
    }

    btnStartCamera.addEventListener('click', startCamera);

    btnSwitchCamera.addEventListener('click', () => {
        currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
        startCamera();
    });

    function stopCamera(fullReset = true) {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        if (scanInterval) { clearInterval(scanInterval); scanInterval = null; }
        if (bboxAnimFrame) { cancelAnimationFrame(bboxAnimFrame); bboxAnimFrame = null; }
        if (bboxFadeTimeout) { clearTimeout(bboxFadeTimeout); bboxFadeTimeout = null; }
        isScanning = false;
        
        if (fullReset) {
            currentBBox = null;
            targetBBox = null;
            lastLiveData = null;
            cameraFeed.srcObject = null;
            cameraOverlay.style.display = 'flex';
            liveIndicator.style.display = 'none';
            btnCapture.style.display = 'none';
            btnSwitchCamera.style.display = 'none';
            detContext.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
            document.getElementById('resultDataContainer').style.display = 'none';
            document.getElementById('resultEmptyState').style.display = 'flex';
        }
    }

    function startScanning() {
        if (scanInterval) clearInterval(scanInterval);
        scanInterval = setInterval(async () => {
            if (!isScanning || cameraFeed.videoWidth === 0) return;
            const context = cameraCanvas.getContext('2d');
            cameraCanvas.width = cameraFeed.videoWidth;
            cameraCanvas.height = cameraFeed.videoHeight;
            detectionCanvas.width = cameraFeed.videoWidth;
            detectionCanvas.height = cameraFeed.videoHeight;
            context.drawImage(cameraFeed, 0, 0, cameraCanvas.width, cameraCanvas.height);
            const base64Image = cameraCanvas.toDataURL('image/jpeg', 0.8);
            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: base64Image })
                });
                const data = await response.json();
                if (data.success && isScanning) {
                    showResults(data, true);
                } else if (isScanning) {
                    // No leaf detected (or rejected by backend)
                    detContext.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
                    if (!lastLiveData) {
                        document.getElementById('resultDataContainer').style.display = 'none';
                        document.getElementById('resultEmptyState').style.display = 'flex';
                    }
                    currentBBox = null;
                    targetBBox = null;
                }
            } catch (err) {
                console.error("Scanning error:", err);
            }
        }, 1000);
    }

    // --- Capture Screenshot ---
    btnCapture.addEventListener('click', () => {
        if (!cameraFeed.srcObject || cameraFeed.videoWidth === 0) return;

        // Create composite canvas
        const captureCanvas = document.createElement('canvas');
        captureCanvas.width = cameraFeed.videoWidth;
        captureCanvas.height = cameraFeed.videoHeight;
        const ctx = captureCanvas.getContext('2d');

        // Draw video frame
        ctx.drawImage(cameraFeed, 0, 0);

        // Draw bounding box overlay
        if (currentBBox && lastBBoxColor) {
            const bbox = currentBBox;
            const x = bbox.x * captureCanvas.width;
            const y = bbox.y * captureCanvas.height;
            const w = bbox.w * captureCanvas.width;
            const h = bbox.h * captureCanvas.height;

            ctx.strokeStyle = lastBBoxColor;
            ctx.lineWidth = 3;
            ctx.setLineDash([8, 4]);
            ctx.strokeRect(x, y, w, h);
            ctx.setLineDash([]);
            ctx.lineWidth = 5;
            const cs = 20;
            // Corners
            ctx.beginPath(); ctx.moveTo(x, y + cs); ctx.lineTo(x, y); ctx.lineTo(x + cs, y); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(x + w - cs, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + cs); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(x, y + h - cs); ctx.lineTo(x, y + h); ctx.lineTo(x + cs, y + h); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(x + w - cs, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + h - cs); ctx.stroke();
            // Label
            if (lastBBoxLabel) {
                ctx.font = '600 14px Inter, sans-serif';
                ctx.fillStyle = lastBBoxColor;
                const tw = ctx.measureText(lastBBoxLabel).width;
                ctx.globalAlpha = 0.85;
                ctx.fillRect(x, y - 28, tw + 16, 28);
                ctx.globalAlpha = 1.0;
                ctx.fillStyle = '#fff';
                ctx.fillText(lastBBoxLabel, x + 8, y - 9);
            }
        }

        // Add result info overlay at bottom
        if (lastLiveData) {
            const pred = lastLiveData.prediction;
            const barH = 40;
            ctx.fillStyle = 'rgba(0,0,0,0.7)';
            ctx.fillRect(0, captureCanvas.height - barH, captureCanvas.width, barH);
            ctx.fillStyle = pred.color;
            ctx.font = '700 16px Inter, sans-serif';
            ctx.fillText(`${pred.label} — ${(pred.confidence * 100).toFixed(1)}%`, 12, captureCanvas.height - 14);
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.font = '400 12px Inter, sans-serif';
            const ts = new Date().toLocaleString('id-ID');
            ctx.fillText(`LeafSense AI • ${ts}`, captureCanvas.width - ctx.measureText(`LeafSense AI • ${ts}`).width - 12, captureCanvas.height - 14);
        }

        // Download
        const link = document.createElement('a');
        link.download = `leafsense_${Date.now()}.png`;
        link.href = captureCanvas.toDataURL('image/png');
        link.click();

        // Flash effect
        btnCapture.classList.add('capture-flash');
        setTimeout(() => btnCapture.classList.remove('capture-flash'), 400);

        // Update stats
        stats.captures++;
        saveStats();
        renderStats();

        // Add to history if we have data
        if (lastLiveData) {
            addToHistory(lastLiveData, 'camera-capture');
        }

        showToast('📸 Screenshot tersimpan!');
    });

    // --- Drag & Drop ---
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
    uploadArea.addEventListener('dragleave', () => { uploadArea.classList.remove('drag-over'); });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) { showError('File harus berupa gambar (PNG, JPG, JPEG, WebP)'); return; }
        if (file.size > 16 * 1024 * 1024) { showError('Ukuran file maksimal 16MB'); return; }
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            uploadArea.style.display = 'none';
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    btnRemove.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        previewContainer.style.display = 'none';
        uploadArea.style.display = 'block';
        document.getElementById('resultDataContainer').style.display = 'none';
        document.getElementById('resultEmptyState').style.display = 'flex';
    });

    // --- Predict (Upload) ---
    btnPredict.addEventListener('click', async () => {
        if (!selectedFile) return;
        const btnText = btnPredict.querySelector('.btn-text');
        const btnLoading = btnPredict.querySelector('.btn-loading');
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';
        btnPredict.disabled = true;

        const formData = new FormData();
        formData.append('file', selectedFile);
        try {
            const response = await fetch('/predict', { method: 'POST', body: formData });
            const data = await response.json();
            if (data.error) { showError(data.error); }
            else if (data.success) { showResults(data, false); }
        } catch (err) {
            showError('Gagal terhubung ke server. Pastikan server berjalan.');
        } finally {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            btnPredict.disabled = false;
        }
    });

    // --- Show Results ---
    function showResults(data, fromCamera = false) {
        const pred = data.prediction;
        const probs = data.probabilities;
        const confidence = pred.confidence;

        // Update stats
        stats.total++;
        if (pred.class && stats[pred.class] !== undefined) stats[pred.class]++;
        saveStats();
        renderStats();

        // Confidence warning removed in UI redesign

        // Common Result UI Update
        document.getElementById('resultEmoji').textContent = pred.emoji;
        document.getElementById('resultLabel').textContent = pred.label;
        document.getElementById('resultLabel').style.color = pred.color;

        const circumference = 2 * Math.PI * 52;
        const offset = circumference * (1 - confidence);
        const ringFill = document.getElementById('ringFill');
        ringFill.style.stroke = pred.color;
        const confValue = document.getElementById('confidenceValue');
        confValue.style.color = pred.color;

        const animDuration = fromCamera ? 0.6 : 1.5;
        ringFill.style.transition = `stroke-dashoffset ${animDuration}s cubic-bezier(0.4, 0, 0.2, 1)`;
        requestAnimationFrame(() => {
            ringFill.style.strokeDashoffset = offset;
            if (fromCamera) {
                confValue.textContent = (confidence * 100).toFixed(1) + '%';
            } else {
                animateCounter(confValue, 0, confidence * 100, 1200);
            }
        });

        document.getElementById('resultDescription').textContent = pred.description;

        const charContainer = document.getElementById('resultCharacteristics');
        charContainer.innerHTML = '';
        (pred.characteristics || []).forEach((c, i) => {
            const tag = document.createElement('span');
            tag.className = 'char-tag';
            tag.textContent = c;
            tag.style.animationDelay = (i * 0.1) + 's';
            charContainer.appendChild(tag);
        });

        const probBars = document.getElementById('probBars');
        probBars.innerHTML = '';
        const colors = { 'daun muda': '#4CAF50', 'daun menguning': '#FF9800', 'daun tua': '#F44336', unknown: '#f59e0b' };
        const labels = { 'daun muda': 'Daun Muda', 'daun menguning': 'Daun Menguning', 'daun tua': 'Daun Tua', unknown: 'Tidak Yakin' };
        Object.keys(probs).forEach(cls => {
            const prob = probs[cls];
            const item = document.createElement('div');
            item.className = 'prob-bar-item';
            item.innerHTML = `
                <div class="prob-bar-header">
                    <span class="prob-bar-label">${labels[cls] || cls}</span>
                    <span class="prob-bar-value" style="color: ${colors[cls] || '#666'}">${(prob * 100).toFixed(2)}%</span>
                </div>
                <div class="prob-bar-track">
                    <div class="prob-bar-fill" style="background: ${colors[cls] || '#666'}; width: 0; transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1)"></div>
                </div>
            `;
            probBars.appendChild(item);
            requestAnimationFrame(() => {
                setTimeout(() => { item.querySelector('.prob-bar-fill').style.width = (prob * 100) + '%'; }, fromCamera ? 0 : 200);
            });
        });

        document.getElementById('resultEmptyState').style.display = 'none';
        document.getElementById('resultDataContainer').style.display = 'block';
        resultsSection.style.display = 'block';
        
        if (fromCamera) {
            lastLiveData = data;
            updateBoundingBox(pred.bbox, pred.color, pred.label);
        } else {
            // Scroll to results only on mobile layout
            if (window.innerWidth < 1024) {
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            addToHistory(data, 'upload');
        }
    }

    // --- Bounding Box Smoothing ---
    function updateBoundingBox(bbox, color, label) {
        lastBBoxColor = color;
        lastBBoxLabel = label;
        if (bboxFadeTimeout) { clearTimeout(bboxFadeTimeout); bboxFadeTimeout = null; }
        if (!bbox) {
            bboxFadeTimeout = setTimeout(() => {
                targetBBox = null; currentBBox = null;
                detContext.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
            }, 2000);
            return;
        }
        targetBBox = { ...bbox };
        if (!currentBBox) currentBBox = { ...bbox };
        if (!bboxAnimFrame) animateBBox();
    }

    function lerp(a, b, t) { return a + (b - a) * t; }

    function animateBBox() {
        if (!isScanning) { bboxAnimFrame = null; return; }
        if (currentBBox && targetBBox) {
            const s = 0.25;
            currentBBox.x = lerp(currentBBox.x, targetBBox.x, s);
            currentBBox.y = lerp(currentBBox.y, targetBBox.y, s);
            currentBBox.w = lerp(currentBBox.w, targetBBox.w, s);
            currentBBox.h = lerp(currentBBox.h, targetBBox.h, s);
            drawBoundingBox(currentBBox, lastBBoxColor, lastBBoxLabel);
        }
        bboxAnimFrame = requestAnimationFrame(animateBBox);
    }

    function drawBoundingBox(bbox, color, label) {
        detContext.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
        if (!bbox) return;

        const cw = detectionCanvas.width;
        const ch = detectionCanvas.height;

        // Mirror x-coordinate to match CSS scaleX(-1) on video feed
        const x = cw - (bbox.x * cw) - (bbox.w * cw);
        const y = bbox.y * ch;
        const w = bbox.w * cw;
        const h = bbox.h * ch;

        // Dashed border
        detContext.strokeStyle = color;
        detContext.lineWidth = 3;
        detContext.setLineDash([8, 4]);
        detContext.lineJoin = 'round';
        detContext.strokeRect(x, y, w, h);

        // Corner accents
        detContext.setLineDash([]);
        detContext.lineWidth = 5;
        const cs = 20;
        detContext.beginPath(); detContext.moveTo(x, y + cs); detContext.lineTo(x, y); detContext.lineTo(x + cs, y); detContext.stroke();
        detContext.beginPath(); detContext.moveTo(x + w - cs, y); detContext.lineTo(x + w, y); detContext.lineTo(x + w, y + cs); detContext.stroke();
        detContext.beginPath(); detContext.moveTo(x, y + h - cs); detContext.lineTo(x, y + h); detContext.lineTo(x + cs, y + h); detContext.stroke();
        detContext.beginPath(); detContext.moveTo(x + w - cs, y + h); detContext.lineTo(x + w, y + h); detContext.lineTo(x + w, y + h - cs); detContext.stroke();

        // Label tag (text drawn normally, not mirrored)
        detContext.fillStyle = color;
        detContext.font = '600 14px Inter, sans-serif';
        const tw = detContext.measureText(label).width;
        detContext.globalAlpha = 0.85;
        detContext.fillRect(x, y - 28, tw + 16, 28);
        detContext.globalAlpha = 1.0;
        detContext.fillStyle = '#fff';
        detContext.fillText(label, x + 8, y - 9);

        // --- Crosshair (center of bbox) ---
        const cx = x + w / 2;
        const cy = y + h / 2;
        const crosshairSize = 15;
        
        detContext.beginPath();
        detContext.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        detContext.lineWidth = 1.5;
        // Inner circle
        detContext.arc(cx, cy, 3, 0, 2 * Math.PI);
        detContext.stroke();
        
        // Horizontal lines
        detContext.beginPath();
        detContext.moveTo(cx - crosshairSize, cy);
        detContext.lineTo(cx - 5, cy);
        detContext.moveTo(cx + 5, cy);
        detContext.lineTo(cx + crosshairSize, cy);
        detContext.stroke();
        
        // Vertical lines
        detContext.beginPath();
        detContext.moveTo(cx, cy - crosshairSize);
        detContext.lineTo(cx, cy - 5);
        detContext.moveTo(cx, cy + 5);
        detContext.lineTo(cx, cy + crosshairSize);
        detContext.stroke();
    }

    // --- History ---
    function addToHistory(data, source) {
        const entry = {
            id: Date.now(),
            timestamp: new Date().toLocaleString('id-ID'),
            label: data.prediction.label,
            class: data.prediction.class,
            confidence: data.prediction.confidence,
            color: data.prediction.color,
            emoji: data.prediction.emoji,
            source: source
        };
        history.unshift(entry);
        if (history.length > 50) history = history.slice(0, 50);
        localStorage.setItem('leafsense_history', JSON.stringify(history));
        renderHistory();
    }

    function renderHistory() {
        const list = document.getElementById('historyList');
        const empty = document.getElementById('historyEmpty');
        if (!list) return;

        if (history.length === 0) {
            list.innerHTML = '';
            list.appendChild(empty || createEmptyState());
            return;
        }

        list.innerHTML = '';
        history.slice(0, 20).forEach(entry => {
            const item = document.createElement('div');
            item.className = 'history-item';
            const srcIcon = entry.source === 'upload' ? '📁' : (entry.source === 'camera-capture' ? '📸' : '📷');
            const confClass = entry.confidence < 0.6 ? 'conf-low' : (entry.confidence > 0.85 ? 'conf-high' : 'conf-mid');
            item.innerHTML = `
                <div class="history-item-left">
                    <span class="history-emoji">${entry.emoji}</span>
                    <div class="history-info">
                        <span class="history-label" style="color:${entry.color}">${entry.label}</span>
                        <span class="history-time">${srcIcon} ${entry.timestamp}</span>
                    </div>
                </div>
                <span class="history-conf ${confClass}">${(entry.confidence * 100).toFixed(1)}%</span>
            `;
            list.appendChild(item);
        });
    }

    function createEmptyState() {
        const div = document.createElement('div');
        div.className = 'history-empty';
        div.id = 'historyEmpty';
        div.innerHTML = '<span>📭</span><p>Belum ada riwayat analisis</p>';
        return div;
    }

    // Clear history
    const btnClearHistory = document.getElementById('btnClearHistory');
    if (btnClearHistory) {
        btnClearHistory.addEventListener('click', () => {
            history = [];
            localStorage.removeItem('leafsense_history');
            stats = { total: 0, 'daun muda': 0, 'daun menguning': 0, 'daun tua': 0, unknown: 0, captures: 0 };
            saveStats();
            renderHistory();
            renderStats();
            showToast('🗑️ Riwayat dan statistik dihapus');
        });
    }

    // --- Stats ---
    function saveStats() {
        localStorage.setItem('leafsense_stats', JSON.stringify(stats));
    }

    function renderStats() {
        const el = (id) => document.getElementById(id);
        if (el('statTotal')) el('statTotal').textContent = stats.total;
        if (el('statMuda')) el('statMuda').textContent = stats['daun muda'] || 0;
        if (el('statSedang')) el('statSedang').textContent = stats['daun menguning'] || 0;
        if (el('statTua')) el('statTua').textContent = stats['daun tua'] || 0;
        if (el('statUnknown')) el('statUnknown').textContent = stats.unknown || 0;
        if (el('statCaptures')) el('statCaptures').textContent = stats.captures || 0;
        
        updateChart();
    }

    // --- Chart Logic ---
    function initChart() {
        const ctx = document.getElementById('statsChart');
        if (!ctx) return;

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";

        statsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Daun Muda', 'Daun Sedang', 'Daun Tua', 'Tidak Yakin'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#4CAF50', // Muda
                        '#FF9800', // Sedang
                        '#F44336', // Tua
                        '#f59e0b'  // Unknown
                    ],
                    borderWidth: 0,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 11, weight: '500' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.9)',
                        titleFont: { size: 13, weight: '700' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: true
                    }
                },
                cutout: '70%',
                animation: {
                    animateScale: true,
                    animateRotate: true,
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    function updateChart() {
        if (!statsChart) return;
        
        const data = [
            stats['daun muda'] || 0,
            stats['daun menguning'] || 0,
            stats['daun tua'] || 0,
            stats.unknown || 0
        ];

        // Only update if there is data to show
        const hasData = data.some(v => v > 0);
        
        // If no data, show a grey placeholder ring
        if (!hasData) {
            statsChart.data.datasets[0].data = [1, 1, 1, 1]; // Equal placeholder
            statsChart.data.datasets[0].backgroundColor = [
                'rgba(255, 255, 255, 0.05)',
                'rgba(255, 255, 255, 0.05)',
                'rgba(255, 255, 255, 0.05)',
                'rgba(255, 255, 255, 0.05)'
            ];
            statsChart.options.plugins.tooltip.enabled = false;
        } else {
            statsChart.data.datasets[0].data = data;
            statsChart.data.datasets[0].backgroundColor = [
                '#4CAF50',
                '#FF9800',
                '#F44336',
                '#f59e0b'
            ];
            statsChart.options.plugins.tooltip.enabled = true;
        }

        statsChart.update();
    }

    // --- Animate Counter ---
    function animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = (start + (end - start) * eased).toFixed(1) + '%';
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    }

    // --- New Analysis ---
    btnNew.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        previewContainer.style.display = 'none';
        uploadArea.style.display = 'block';
        
        document.getElementById('resultDataContainer').style.display = 'none';
        document.getElementById('resultEmptyState').style.display = 'flex';
        
        const isLiveTab = document.getElementById('liveCameraTab').classList.contains('active');
        if (!isLiveTab) {
            stopCamera();
            uploadSectionContainer.scrollIntoView({ behavior: 'smooth' });
        }
    });

    // --- Toast ---
    function showError(msg) {
        errorMessage.textContent = msg;
        errorToast.style.display = 'flex';
        setTimeout(() => { errorToast.style.display = 'none'; }, 5000);
    }

    function showToast(msg) {
        errorMessage.textContent = msg;
        errorToast.style.background = 'rgba(34, 197, 94, 0.9)';
        errorToast.style.boxShadow = '0 8px 32px rgba(34, 197, 94, 0.3)';
        errorToast.style.display = 'flex';
        setTimeout(() => {
            errorToast.style.display = 'none';
            errorToast.style.background = '';
            errorToast.style.boxShadow = '';
        }, 3000);
    }

    // --- Scroll Reveal Animations ---
    const revealSections = document.querySelectorAll('.stats-section, .history-section, .info-section');
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });
    revealSections.forEach(s => {
        s.style.opacity = '0';
        s.style.transform = 'translateY(30px)';
        s.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
        revealObserver.observe(s);
    });

    // Apply the revealed class
    const style = document.createElement('style');
    style.textContent = '.revealed { opacity: 1 !important; transform: translateY(0) !important; }';
    document.head.appendChild(style);

    // --- Cursor Glow Effect (Desktop only) ---
    const glowEl = document.createElement('div');
    glowEl.style.cssText = `
        position: fixed; width: 300px; height: 300px; border-radius: 50%;
        background: radial-gradient(circle, rgba(34,197,94,0.06), transparent 70%);
        pointer-events: none; z-index: 0; transform: translate(-50%, -50%);
        transition: left 0.3s ease, top 0.3s ease;
    `;
    document.body.appendChild(glowEl);
    document.addEventListener('mousemove', (e) => {
        glowEl.style.left = e.clientX + 'px';
        glowEl.style.top = e.clientY + 'px';
    });

    // --- Grad-CAM Logic ---
    const gradcamModal = document.getElementById('gradcamModal');
    const gradcamModalClose = document.getElementById('gradcamModalClose');
    const gradcamImage = document.getElementById('gradcamImage');

    const btnGradcamUpload = document.getElementById('btnGradcamUpload');

    function showGradcamModal(imageSrc) {
        gradcamImage.src = imageSrc;
        gradcamModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function hideGradcamModal() {
        gradcamModal.style.display = 'none';
        document.body.style.overflow = '';
    }

    gradcamModalClose.addEventListener('click', hideGradcamModal);
    gradcamModal.addEventListener('click', (e) => {
        if (e.target === gradcamModal) hideGradcamModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && gradcamModal.style.display === 'flex') hideGradcamModal();
    });

    async function requestGradcam(btn, imageData) {
        const btnText = btn.querySelector('.btn-text');
        const btnLoading = btn.querySelector('.btn-loading');
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';
        btn.disabled = true;

        try {
            const response = await fetch('/gradcam', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            });
            const data = await response.json();
            if (data.success && data.gradcam_image) {
                showGradcamModal(data.gradcam_image);
            } else {
                showError(data.error || 'Gagal membuat Grad-CAM');
            }
        } catch (err) {
            showError('Gagal terhubung ke server untuk Grad-CAM');
        } finally {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            btn.disabled = false;
        }
    }



    // Grad-CAM from uploaded image
    btnGradcamUpload.addEventListener('click', () => {
        if (!previewImage.src || previewImage.src === '') return;
        requestGradcam(btnGradcamUpload, previewImage.src);
    });

    // --- Compare Mode Logic ---
    function setupCompareSlot(side, uploadArea, input, preview) {
        uploadArea.addEventListener('click', () => input.click());
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                if (!file.type.startsWith('image/')) { showError('File harus berupa gambar'); return; }
                compareFiles[side] = file;
                const reader = new FileReader();
                reader.onload = (ev) => {
                    preview.querySelector('img').src = ev.target.result;
                    uploadArea.style.display = 'none';
                    preview.style.display = 'block';
                    document.getElementById(`compareResult${side.charAt(0).toUpperCase() + side.slice(1)}`).style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    setupCompareSlot('left', compareUploadLeft, compareInputLeft, comparePreviewLeft);
    setupCompareSlot('right', compareUploadRight, compareInputRight, comparePreviewRight);

    btnSlotRemoves.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const side = btn.getAttribute('data-slot');
            compareFiles[side] = null;
            const input = side === 'left' ? compareInputLeft : compareInputRight;
            const uploadArea = side === 'left' ? compareUploadLeft : compareUploadRight;
            const preview = side === 'left' ? comparePreviewLeft : comparePreviewRight;
            const result = side === 'left' ? compareResultLeft : compareResultRight;
            
            input.value = '';
            preview.style.display = 'none';
            uploadArea.style.display = 'flex';
            if (result) result.style.display = 'none';
            e.stopPropagation();
        });
    });

    btnCompare.addEventListener('click', async () => {
        if (!compareFiles.left || !compareFiles.right) {
            showError('Pilih kedua gambar terlebih dahulu untuk dibandingkan');
            return;
        }

        const btnText = btnCompare.querySelector('.btn-text');
        const btnLoading = btnCompare.querySelector('.btn-loading');
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';
        btnCompare.disabled = true;

        try {
            // Predict both in parallel
            const promiseLeft = predictFile(compareFiles.left);
            const promiseRight = predictFile(compareFiles.right);
            
            const [resLeft, resRight] = await Promise.all([promiseLeft, promiseRight]);
            
            if (resLeft.success) renderCompareResult('Left', resLeft);
            else showError('Gagal menganalisis gambar 1: ' + (resLeft.error || 'Unknown error'));
            
            if (resRight.success) renderCompareResult('Right', resRight);
            else showError('Gagal menganalisis gambar 2: ' + (resRight.error || 'Unknown error'));

        } catch (err) {
            showError('Terjadi kesalahan saat membandingkan');
            console.error(err);
        } finally {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            btnCompare.disabled = false;
        }
    });

    async function predictFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch('/predict', { method: 'POST', body: formData });
        return await response.json();
    }

    function renderCompareResult(side, data) {
        const container = document.getElementById(`compareResult${side}`);
        const pred = data.prediction;
        const probs = data.probabilities;
        
        container.innerHTML = `
            <div class="compare-result-header">
                <span class="compare-result-emoji">${pred.emoji}</span>
                <span class="compare-result-label" style="color:${pred.color}">${pred.label}</span>
            </div>
            <div class="compare-prob-mini">
                ${Object.keys(probs).map(cls => `
                    <div class="compare-prob-item">
                        <div class="prob-bar-header">
                            <span>${cls.toUpperCase()}</span>
                            <span>${(probs[cls] * 100).toFixed(1)}%</span>
                        </div>
                        <div class="prob-bar-track" style="height:4px">
                            <div class="prob-bar-fill" style="width:${probs[cls] * 100}%; background: ${pred.class === cls ? pred.color : '#444'}"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top:12px; font-size:0.75rem; color:var(--text-muted); line-height:1.4;">
                Confidence: ${(pred.confidence * 100).toFixed(1)}%
            </div>
        `;
        container.style.display = 'block';
    }
});
