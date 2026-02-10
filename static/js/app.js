/**
 * Captcha Generator - Frontend JavaScript
 * Handles all captcha interactions
 */

// ===== Tab Navigation =====
const tabBtns = document.querySelectorAll('.tab-btn');
const panels = document.querySelectorAll('.panel');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        tabBtns.forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');

        panels.forEach(p => p.classList.remove('active'));
        document.getElementById(`${tab}-panel`).classList.add('active');

        // Load captcha for the selected tab
        loadCaptchaForTab(tab);
    });
});

function loadCaptchaForTab(tab) {
    switch (tab) {
        case 'text': loadTextCaptcha(); break;
        case 'image': loadImageCaptcha(); break;
        case 'cloudflare': loadCloudflareCaptcha(); break;
        case 'sliding': loadSlidingPuzzle(); break;
        case 'drag': loadDragPuzzle(); break;
    }
}

function showResult(elementId, success, message) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = `result-message show ${success ? 'success' : 'error'}`;
    setTimeout(() => el.classList.remove('show'), 3000);
}

// ===== Text Captcha =====
async function loadTextCaptcha() {
    try {
        const res = await fetch('/api/text-captcha');
        const data = await res.json();
        document.getElementById('text-captcha-image').src = data.image;
        document.getElementById('text-captcha-input').value = '';
        document.getElementById('text-captcha-input').maxLength = data.length;
    } catch (e) {
        console.error('Failed to load text captcha:', e);
    }
}

document.getElementById('refresh-text-captcha').addEventListener('click', loadTextCaptcha);

document.getElementById('verify-text-captcha').addEventListener('click', async () => {
    const answer = document.getElementById('text-captcha-input').value;
    try {
        const res = await fetch('/api/text-captcha/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer })
        });
        const data = await res.json();
        showResult('text-result', data.success, data.message);
        if (!data.success) {
            document.getElementById('text-captcha-input').classList.add('shake');
            setTimeout(() => document.getElementById('text-captcha-input').classList.remove('shake'), 400);
        }
    } catch (e) {
        console.error('Verification failed:', e);
    }
});

document.getElementById('text-captcha-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') document.getElementById('verify-text-captcha').click();
});

// ===== Image Captcha =====
let selectedImageIndices = [];
let requiredSelections = 3;

async function loadImageCaptcha() {
    selectedImageIndices = [];
    try {
        const res = await fetch('/api/image-captcha');
        const data = await res.json();
        document.getElementById('image-captcha-prompt').textContent = data.prompt;
        requiredSelections = data.required_selections || 3;

        // Update selection counter
        updateSelectionCounter();

        const grid = document.getElementById('image-captcha-grid');
        grid.innerHTML = '';

        data.images.forEach((img, i) => {
            const div = document.createElement('div');
            div.className = 'image-option';
            div.dataset.index = img.index;
            div.innerHTML = `<img src="${img.image}" alt="Option ${i + 1}">`;
            div.addEventListener('click', () => toggleImageSelection(div, img.index));
            grid.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to load image captcha:', e);
    }
}

function toggleImageSelection(element, index) {
    const idx = selectedImageIndices.indexOf(index);

    if (idx > -1) {
        // Deselect
        selectedImageIndices.splice(idx, 1);
        element.classList.remove('selected');
    } else {
        // Select (only if we haven't reached the limit)
        if (selectedImageIndices.length < requiredSelections) {
            selectedImageIndices.push(index);
            element.classList.add('selected');
        }
    }

    updateSelectionCounter();
}

function updateSelectionCounter() {
    const counter = document.getElementById('selection-counter');
    if (counter) {
        counter.textContent = `Selected: ${selectedImageIndices.length}/${requiredSelections}`;
    }
}

async function verifyImageCaptcha() {
    if (selectedImageIndices.length !== requiredSelections) {
        showResult('image-result', false, `Please select exactly ${requiredSelections} images.`);
        return;
    }

    try {
        const res = await fetch('/api/image-captcha/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected_indices: selectedImageIndices })
        });
        const data = await res.json();
        showResult('image-result', data.success, data.message);
        if (!data.success) {
            setTimeout(loadImageCaptcha, 1500);
        }
    } catch (e) {
        console.error('Verification failed:', e);
    }
}

document.getElementById('refresh-image-captcha').addEventListener('click', loadImageCaptcha);
document.getElementById('verify-image-captcha').addEventListener('click', verifyImageCaptcha);

// ===== Cloudflare Captcha =====
let cfVerified = false;

async function loadCloudflareCaptcha() {
    cfVerified = false;
    const widget = document.getElementById('cloudflare-widget');
    const checkbox = document.getElementById('cf-checkbox');
    const spinner = document.getElementById('cf-spinner');
    const success = document.getElementById('cf-success');

    widget.classList.remove('verifying', 'verified');
    checkbox.checked = false;
    spinner.classList.remove('show');
    success.classList.remove('show');

    try {
        await fetch('/api/cloudflare-captcha');
    } catch (e) {
        console.error('Failed to load cloudflare captcha:', e);
    }
}

document.getElementById('cf-checkbox').addEventListener('change', async function () {
    if (cfVerified) return;

    const widget = document.getElementById('cloudflare-widget');
    const spinner = document.getElementById('cf-spinner');
    const successEl = document.getElementById('cf-success');

    if (this.checked) {
        widget.classList.add('verifying');
        spinner.classList.add('show');

        try {
            const res = await fetch('/api/cloudflare-captcha/complete', { method: 'POST' });
            const data = await res.json();

            await new Promise(r => setTimeout(r, 1000));

            spinner.classList.remove('show');

            if (data.success) {
                widget.classList.remove('verifying');
                widget.classList.add('verified');
                successEl.classList.add('show');
                cfVerified = true;
                showResult('cloudflare-result', true, 'Verification successful!');
            } else {
                widget.classList.remove('verifying');
                this.checked = false;
                showResult('cloudflare-result', false, data.error || 'Verification failed');
            }
        } catch (e) {
            spinner.classList.remove('show');
            widget.classList.remove('verifying');
            this.checked = false;
            console.error('Cloudflare verification failed:', e);
        }
    }
});

document.getElementById('refresh-cloudflare-captcha').addEventListener('click', loadCloudflareCaptcha);

// ===== Sliding Puzzle =====
let slidingData = null;

async function loadSlidingPuzzle() {
    try {
        const res = await fetch('/api/puzzle-captcha/sliding');
        slidingData = await res.json();

        document.getElementById('sliding-bg').src = slidingData.background;

        const piece = document.getElementById('sliding-piece');
        piece.src = slidingData.piece;
        piece.style.top = `${slidingData.piece_y - 10}px`;
        piece.style.left = '0px';

        const slider = document.getElementById('puzzle-slider');
        slider.value = 0;
        slider.max = slidingData.puzzle_width - slidingData.piece_size;

        document.getElementById('slider-progress').style.width = '0%';
    } catch (e) {
        console.error('Failed to load sliding puzzle:', e);
    }
}

document.getElementById('puzzle-slider').addEventListener('input', function () {
    const piece = document.getElementById('sliding-piece');
    piece.style.left = `${this.value - 10}px`;

    const progress = (this.value / this.max) * 100;
    document.getElementById('slider-progress').style.width = `${progress}%`;
});

document.getElementById('verify-sliding').addEventListener('click', async () => {
    const sliderValue = parseInt(document.getElementById('puzzle-slider').value);

    try {
        const res = await fetch('/api/puzzle-captcha/sliding/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x: sliderValue })
        });
        const data = await res.json();
        showResult('sliding-result', data.success, data.message);
        if (!data.success) {
            setTimeout(loadSlidingPuzzle, 1500);
        }
    } catch (e) {
        console.error('Sliding verification failed:', e);
    }
});

document.getElementById('refresh-sliding-captcha').addEventListener('click', loadSlidingPuzzle);

// ===== Drag Puzzle =====
let dragData = null;
let placedPieces = {};

async function loadDragPuzzle() {
    placedPieces = {};

    try {
        const res = await fetch('/api/puzzle-captcha/drag');
        dragData = await res.json();

        document.getElementById('drag-bg').src = dragData.background;

        // Create drop zones
        const dropZones = document.getElementById('drop-zones');
        dropZones.innerHTML = '';

        dragData.positions.forEach(pos => {
            const zone = document.createElement('div');
            zone.className = 'drop-zone';
            zone.dataset.id = pos.id;
            zone.style.left = `${pos.x}px`;
            zone.style.top = `${pos.y}px`;
            zone.style.width = `${dragData.piece_size}px`;
            zone.style.height = `${dragData.piece_size}px`;
            zone.textContent = pos.id + 1;
            dropZones.appendChild(zone);
        });

        // Create draggable pieces in tray
        const tray = document.getElementById('pieces-tray');
        tray.innerHTML = '';

        dragData.pieces.forEach(piece => {
            const pieceEl = document.createElement('div');
            pieceEl.className = 'draggable-piece';
            pieceEl.dataset.id = piece.id;
            pieceEl.innerHTML = `<img src="${piece.image}" alt="Piece ${piece.id + 1}">`;
            pieceEl.draggable = true;

            pieceEl.addEventListener('dragstart', handleDragStart);
            pieceEl.addEventListener('dragend', handleDragEnd);

            tray.appendChild(pieceEl);
        });

        // Set up drop zone events
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.addEventListener('dragover', handleDragOver);
            zone.addEventListener('dragleave', handleDragLeave);
            zone.addEventListener('drop', handleDrop);
        });

        // Also allow dropping back to tray
        tray.addEventListener('dragover', handleDragOver);
        tray.addEventListener('drop', handleDropToTray);

    } catch (e) {
        console.error('Failed to load drag puzzle:', e);
    }
}

let draggedPieceId = null;

function handleDragStart(e) {
    draggedPieceId = parseInt(e.target.dataset.id);
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (e.currentTarget.classList.contains('drop-zone')) {
        e.currentTarget.classList.add('highlight');
    }
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('highlight');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('highlight');

    const zoneId = parseInt(e.currentTarget.dataset.id);
    const zone = e.currentTarget;

    // Find the piece element
    const pieceEl = document.querySelector(`.draggable-piece[data-id="${draggedPieceId}"]`);
    if (!pieceEl) return;

    // Remove from current position
    if (placedPieces[draggedPieceId] !== undefined) {
        delete placedPieces[draggedPieceId];
    }

    // Check if zone already has a piece
    Object.keys(placedPieces).forEach(id => {
        if (placedPieces[id] === zoneId) {
            // Move that piece back to tray
            const otherPiece = document.querySelector(`.draggable-piece[data-id="${id}"]`);
            if (otherPiece) {
                document.getElementById('pieces-tray').appendChild(otherPiece);
                otherPiece.classList.remove('placed');
            }
            delete placedPieces[id];
        }
    });

    // Place piece in zone
    placedPieces[draggedPieceId] = zoneId;

    const board = document.getElementById('drag-puzzle-board');
    board.appendChild(pieceEl);
    pieceEl.classList.add('placed');

    const pos = dragData.positions.find(p => p.id === zoneId);
    pieceEl.style.left = `${pos.x}px`;
    pieceEl.style.top = `${pos.y}px`;
}

function handleDropToTray(e) {
    e.preventDefault();

    const pieceEl = document.querySelector(`.draggable-piece[data-id="${draggedPieceId}"]`);
    if (!pieceEl) return;

    if (placedPieces[draggedPieceId] !== undefined) {
        delete placedPieces[draggedPieceId];
    }

    pieceEl.classList.remove('placed');
    pieceEl.style.left = '';
    pieceEl.style.top = '';
    document.getElementById('pieces-tray').appendChild(pieceEl);
}

document.getElementById('verify-drag').addEventListener('click', async () => {
    // Build positions array
    const positions = Object.keys(placedPieces).map(pieceId => {
        const zoneId = placedPieces[pieceId];
        const pos = dragData.positions.find(p => p.id === zoneId);
        return {
            id: parseInt(pieceId),
            x: pos.x,
            y: pos.y
        };
    });

    try {
        const res = await fetch('/api/puzzle-captcha/drag/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ positions })
        });
        const data = await res.json();
        showResult('drag-result', data.success, data.message);
        if (!data.success) {
            setTimeout(loadDragPuzzle, 1500);
        }
    } catch (e) {
        console.error('Drag verification failed:', e);
    }
});

document.getElementById('refresh-drag-captcha').addEventListener('click', loadDragPuzzle);

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    loadTextCaptcha();
});
