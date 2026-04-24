/**
 * LeafSense AI - Frontend Logic
 * Drag & Drop, AJAX upload, result rendering, Live Camera
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
    const cameraOverlay = document.getElementById('cameraOverlay');
    const btnStartCamera = document.getElementById('btnStartCamera');
    const liveIndicator = document.getElementById('liveIndicator');

    let selectedFile = null;
    let cameraStream = null;
    let scanInterval = null;
    let isScanning = false;

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
    createParticles();

    // --- Tabs Logic ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).style.display = 'block';

            // Stop camera if switching away from live camera
            if (targetId !== 'liveCameraTab') {
                stopCamera();
            }
        });
    });

    // --- Camera Logic ---
    btnStartCamera.addEventListener('click', async () => {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            cameraFeed.srcObject = cameraStream;
            cameraOverlay.style.display = 'none';
            liveIndicator.style.display = 'flex';
            
            // Start scanning loop
            isScanning = true;
            startScanning();
            
            // Show results immediately empty
            resultsSection.style.display = 'block';
            
        } catch (err) {
            showError('Akses kamera ditolak atau kamera tidak ditemukan.');
        }
    });

    function stopCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        if (scanInterval) {
            clearInterval(scanInterval);
            scanInterval = null;
        }
        isScanning = false;
        cameraFeed.srcObject = null;
        cameraOverlay.style.display = 'flex';
        liveIndicator.style.display = 'none';
    }

    function startScanning() {
        if (scanInterval) clearInterval(scanInterval);
        
        scanInterval = setInterval(async () => {
            if (!isScanning) return;
            
            if (cameraFeed.videoWidth === 0) return; // Wait for video to be ready
            
            // Capture frame
            const context = cameraCanvas.getContext('2d');
            cameraCanvas.width = cameraFeed.videoWidth;
            cameraCanvas.height = cameraFeed.videoHeight;
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
                    showResults(data, true); // true = from camera
                }
            } catch (err) {
                console.error("Scanning error:", err);
            }
            
        }, 1500); // Scan every 1.5 seconds
    }

    // --- Drag & Drop ---
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    // --- File Handling ---
    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showError('File harus berupa gambar (PNG, JPG, JPEG, WebP)');
            return;
        }
        if (file.size > 16 * 1024 * 1024) {
            showError('Ukuran file maksimal 16MB');
            return;
        }

        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            uploadArea.style.display = 'none';
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    // --- Remove Image ---
    btnRemove.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        previewContainer.style.display = 'none';
        uploadArea.style.display = 'block';
        resultsSection.style.display = 'none';
    });

    // --- Predict (for Upload mode) ---
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
            const response = await fetch('/predict', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                showError(data.error);
            } else if (data.success) {
                showResults(data, false);
            }
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

        // Main result
        document.getElementById('resultEmoji').textContent = pred.emoji;
        document.getElementById('resultLabel').textContent = pred.label;
        document.getElementById('resultLabel').style.color = pred.color;

        // Confidence ring
        const confidence = pred.confidence;
        const circumference = 2 * Math.PI * 52; // r=52
        const offset = circumference * (1 - confidence);
        const ringFill = document.getElementById('ringFill');
        ringFill.style.stroke = pred.color;
        
        const confValue = document.getElementById('confidenceValue');
        confValue.style.color = pred.color;

        if (!fromCamera) {
            // Animate slowly if from upload
            ringFill.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
            requestAnimationFrame(() => {
                ringFill.style.strokeDashoffset = offset;
                animateCounter(confValue, 0, confidence * 100, 1200);
            });
        } else {
            // Quick update without long animation for live feed
            ringFill.style.transition = 'stroke-dashoffset 0.3s ease';
            ringFill.style.strokeDashoffset = offset;
            confValue.textContent = (confidence * 100).toFixed(1) + '%';
        }

        // Description
        document.getElementById('resultDescription').textContent = pred.description;

        // Characteristics
        const charContainer = document.getElementById('resultCharacteristics');
        charContainer.innerHTML = '';
        (pred.characteristics || []).forEach((char, i) => {
            const tag = document.createElement('span');
            tag.className = 'char-tag';
            tag.textContent = char;
            if (!fromCamera) tag.style.animationDelay = (i * 0.1) + 's';
            else tag.style.animation = 'none'; // no fade in for live
            charContainer.appendChild(tag);
        });

        // Probability bars
        const probBars = document.getElementById('probBars');
        probBars.innerHTML = '';
        const colors = { muda: '#4CAF50', sedang: '#FF9800', tua: '#F44336' };
        const labels = { muda: 'Daun Muda', sedang: 'Daun Sedang', tua: 'Daun Tua' };

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
                    <div class="prob-bar-fill" style="background: ${colors[cls] || '#666'}; width: ${fromCamera ? (prob * 100) + '%' : '0'}; transition: ${fromCamera ? 'width 0.3s ease' : 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)'}"></div>
                </div>
            `;
            probBars.appendChild(item);

            if (!fromCamera) {
                requestAnimationFrame(() => {
                    setTimeout(() => {
                        item.querySelector('.prob-bar-fill').style.width = (prob * 100) + '%';
                    }, 200);
                });
            }
        });

        // Show results section
        resultsSection.style.display = 'block';
        if (!fromCamera) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // --- Animate Counter ---
    function animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            const value = start + (end - start) * eased;
            element.textContent = value.toFixed(1) + '%';
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
        resultsSection.style.display = 'none';
        
        // Stop scanning but keep camera open if in camera tab
        // Actually, btnNew usually means user wants to start over. 
        // If they are in upload mode, just scroll up. If in live mode, reset.
        const isLiveTab = document.getElementById('liveCameraTab').classList.contains('active');
        if (!isLiveTab) {
            stopCamera();
            uploadSectionContainer.scrollIntoView({ behavior: 'smooth' });
        }
    });

    // --- Error Toast ---
    function showError(msg) {
        errorMessage.textContent = msg;
        errorToast.style.display = 'flex';
        setTimeout(() => { errorToast.style.display = 'none'; }, 5000);
    }
});
