/**
 * SeatFlow — app.js
 * Connects to FastAPI backend at API_BASE
 */

'use strict';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

let state = {
  seats:         2,
  token:         null,
  username:      null,
  countdownSec:  15 * 60,
  countdownInt:  null,
  gameLoop:      null,
  cart:          {},
  reservationId: null,
};

const $ = id => document.getElementById(id);

const els = {
  availableSeats: $('availableSeats'),
  totalSeats:     $('totalSeats'),
  progressFill:   $('progressFill'),
  progressGlow:   $('progressGlow'),
  availStatus:    $('availStatus'),
  refreshBtn:     $('refreshBtn'),
  seatCount:      $('seatCount'),
  seatMinus:      $('seatMinus'),
  seatPlus:       $('seatPlus'),
  guestName:      $('guestName'),
  guestContact:   $('guestContact'),
  notes:          $('notes'),
  reservationDatetime: $('reservationDatetime'),
  reservationForm:$('reservationForm'),
  submitBtn:      $('submitBtn'),
  authSection:    $('authSection'),
  formSection:    $('formSection'),
  loggedInBar:    $('loggedInBar'),
  loggedInName:   $('loggedInName'),
  logoutBtn:      $('logoutBtn'),
  successModal:   $('successModal'),
  confirmCode:    $('confirmationCode'),
  countdownTime:  $('countdownTime'),
  ringProgress:   $('ringProgress'),
  modalClose:     $('modalClose'),
  gameModal:      $('gameModal'),
  gameBtn:        $('gameBtn'),
  gameModalClose: $('gameModalClose'),
  gameCanvas:     $('gameCanvas'),
  adminModal:     $('adminModal'),
  adminBtn:       $('adminBtn'),
  adminModalClose:$('adminModalClose'),
  adminUser:      $('adminUser'),
  adminPass:      $('adminPass'),
  adminLoginBtn:  $('adminLoginBtn'),
  adminStatus:    $('adminStatus'),
  authModal:      $('authModal'),
  tabLogin:       $('tabLogin'),
  tabRegister:    $('tabRegister'),
  loginForm:      $('loginForm'),
  registerForm:   $('registerForm'),
  loginUser:      $('loginUser'),
  loginPass:      $('loginPass'),
  loginBtn:       $('loginBtn'),
  loginStatus:    $('loginStatus'),
  regFullName:    $('regFullName'),
  regUsername:    $('regUsername'),
  regEmail:       $('regEmail'),
  regPass:        $('regPass'),
  registerBtn:    $('registerBtn'),
  registerStatus: $('registerStatus'),
  toast:          $('toast'),
  menuSection:       $('menuSection'),
  menuCategories:    $('menuCategories'),
  cartWrap:          $('cartWrap'),
  cartItems:         $('cartItems'),
  cartCount:         $('cartCount'),
  cartTotal:         $('cartTotal'),
  orderSubmitBtn:    $('orderSubmitBtn'),
  orderConfirmation: $('orderConfirmation'),
  orderConfItems:    $('orderConfItems'),
  orderEditBtn:      $('orderEditBtn'),
  myReservationsSection: $('myReservationsSection'),
  myReservationsList:    $('myReservationsList'),
  myResBtn:              $('myResBtn'),
  checkInModal:          $('checkInModal'),
  checkInInput:          $('checkInInput'),
  checkInBtn:            $('checkInBtn'),
  checkInStatus:         $('checkInStatus'),
  checkInModalClose:     $('checkInModalClose'),
};

let toastTimer = null;
function showToast(msg, type = '') {
  clearTimeout(toastTimer);
  els.toast.textContent = msg;
  els.toast.className   = `toast ${type} show`;
  toastTimer = setTimeout(() => { els.toast.className = 'toast'; }, 3200);
}

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
  const res  = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail || `Error ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

function setLoggedIn(token, username) {
  state.token    = token;
  state.username = username;
  sessionStorage.setItem('sf_token',    token);
  sessionStorage.setItem('sf_username', username);
  els.authSection.style.display = 'none';
  els.formSection.style.display = 'block';
  els.loggedInBar.style.display = 'flex';
  els.loggedInName.textContent  = username;
  els.menuSection.style.display = 'none';
  loadMyReservations();
}

function setLoggedOut() {
  state.token         = null;
  state.username      = null;
  state.reservationId = null;
  sessionStorage.removeItem('sf_token');
  sessionStorage.removeItem('sf_username');
  els.authSection.style.display           = 'block';
  els.formSection.style.display           = 'none';
  els.loggedInBar.style.display           = 'none';
  els.menuSection.style.display           = 'none';
  els.myReservationsSection.style.display = 'none';
}

const savedToken    = sessionStorage.getItem('sf_token');
const savedUsername = sessionStorage.getItem('sf_username');
if (savedToken && savedUsername) { setLoggedIn(savedToken, savedUsername); }
else { setLoggedOut(); }

els.logoutBtn.addEventListener('click', () => { setLoggedOut(); showToast('Ausgeloggt', ''); });

els.tabLogin.addEventListener('click', () => {
  els.tabLogin.classList.add('active');
  els.tabRegister.classList.remove('active');
  els.loginForm.style.display    = 'flex';
  els.registerForm.style.display = 'none';
});
els.tabRegister.addEventListener('click', () => {
  els.tabRegister.classList.add('active');
  els.tabLogin.classList.remove('active');
  els.registerForm.style.display = 'flex';
  els.loginForm.style.display    = 'none';
});

els.loginBtn.addEventListener('click', async () => {
  const username = els.loginUser.value.trim();
  const password = els.loginPass.value.trim();
  if (!username || !password) {
    els.loginStatus.textContent = 'Bitte alle Felder ausfüllen.';
    els.loginStatus.style.color = 'var(--red)'; return;
  }
  els.loginBtn.disabled = true;
  els.loginStatus.textContent = 'Wird eingeloggt…';
  els.loginStatus.style.color = 'var(--text-muted)';
  try {
    const data = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
    setLoggedIn(data.access_token, username);
    closeModal(els.authModal);
    showToast(`Willkommen, ${username}! 👋`, 'success');
    els.loginUser.value = ''; els.loginPass.value = ''; els.loginStatus.textContent = '';
  } catch {
    els.loginStatus.textContent = 'Falscher Benutzername oder Passwort.';
    els.loginStatus.style.color = 'var(--red)';
  } finally { els.loginBtn.disabled = false; }
});

els.registerBtn.addEventListener('click', async () => {
  const full_name = els.regFullName.value.trim();
  const username  = els.regUsername.value.trim();
  const email     = els.regEmail.value.trim();
  const password  = els.regPass.value.trim();
  if (!full_name || !username || !email || !password) {
    els.registerStatus.textContent = 'Bitte alle Felder ausfüllen.';
    els.registerStatus.style.color = 'var(--red)'; return;
  }
  els.registerBtn.disabled = true;
  els.registerStatus.textContent = 'Konto wird erstellt…';
  els.registerStatus.style.color = 'var(--text-muted)';
  try {
    await apiFetch('/auth/register', { method: 'POST', body: JSON.stringify({ full_name, username, email, password }) });
    const loginData = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
    setLoggedIn(loginData.access_token, username);
    closeModal(els.authModal);
    showToast(`Konto erstellt! Willkommen, ${username} 🎉`, 'success');
    els.regFullName.value = ''; els.regUsername.value = '';
    els.regEmail.value = ''; els.regPass.value = '';
    els.registerStatus.textContent = '';
  } catch (err) {
    els.registerStatus.textContent = err.message;
    els.registerStatus.style.color = 'var(--red)';
  } finally { els.registerBtn.disabled = false; }
});

async function loadAvailability() {
  els.refreshBtn.classList.add('spinning');
  try {
    const data = await apiFetch('/seats/availability');
    const available  = data.available_seats  ?? 0;
    const reservable = data.reservable_seats ?? 0;
    const reserved   = data.reserved_seats   ?? 0;
    const occupancy  = reservable > 0 ? (reserved / reservable) : 0;
    const freePct    = reservable > 0 ? ((available / reservable) * 100).toFixed(0) : 0;
    els.availableSeats.classList.remove('number-pop');
    void els.availableSeats.offsetWidth;
    els.availableSeats.classList.add('number-pop');
    els.availableSeats.textContent = available;
    els.totalSeats.textContent     = `/ ${reservable}`;
    const fillPct = (occupancy * 100).toFixed(1);
    els.progressFill.style.width = fillPct + '%';
    els.progressGlow.style.width = fillPct + '%';
    if (available === 0) {
      els.availStatus.textContent = '🔴 Ausgebucht';
      els.availStatus.style.color = 'var(--red)';
    } else if (available <= 5) {
      els.availStatus.textContent = `⚠️ Nur noch ${available} Plätze frei`;
      els.availStatus.style.color = '#e07a2a';
    } else {
      els.availStatus.textContent = `${freePct}% der Plätze verfügbar`;
      els.availStatus.style.color = '';
    }
    if (state.seats > available) { state.seats = Math.max(1, available); els.seatCount.textContent = state.seats; }
  } catch {
    els.availStatus.textContent = 'Konnte nicht laden';
    showToast('Verbindung fehlgeschlagen', 'error');
  } finally { setTimeout(() => els.refreshBtn.classList.remove('spinning'), 600); }
}
setInterval(loadAvailability, 30_000);

els.seatMinus.addEventListener('click', () => { if (state.seats > 1)  { state.seats--; els.seatCount.textContent = state.seats; } });
els.seatPlus.addEventListener('click',  () => { if (state.seats < 20) { state.seats++; els.seatCount.textContent = state.seats; } });

els.reservationForm.addEventListener('submit', async e => {
  e.preventDefault();
  const name        = els.guestName.value.trim();
  const contact     = els.guestContact.value.trim();
  const notes       = els.notes.value.trim();
  const datetimeVal = els.reservationDatetime?.value || '';

  if (!name)    return showToast('Bitte deinen Namen eingeben', 'error');
  if (!contact) return showToast('Bitte Telefon oder E-Mail eingeben', 'error');

  els.submitBtn.disabled = true;
  els.submitBtn.querySelector('.submit-text').textContent = 'Wird gesendet…';
  try {
    const res = await apiFetch('/reservations', {
      method: 'POST',
      body: JSON.stringify({
        guest_name:           name,
        guest_contact:        contact,
        seats_reserved:       state.seats,
        notes:                notes || null,
        reservation_datetime: datetimeVal ? new Date(datetimeVal).toISOString() : null,
      }),
    });
    state.reservationId = res.id;
    els.confirmCode.textContent = res.confirmation_code;

    // Zeige Ankunftszeit im Modal wenn Vorausreservierung
    if (res.reservation_datetime) {
      const dt = new Date(res.reservation_datetime);
      const formatted = dt.toLocaleDateString('de-DE', {
        weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
      showToast(`Reserviert für ${formatted} 🗓️`, 'success');
    }

    openModal(els.successModal);
startCountdown(res.reservation_datetime);
loadMyReservations();
setTimeout(() => {
  if (confirm('Möchtest du jetzt vorbestellen? 🍺\n\nJa = Menü wird angezeigt\nNein = Später bestellen')) {
    showMenuSection();
  }
}, 500);
    els.guestName.value = ''; els.guestContact.value = ''; els.notes.value = '';
    if (els.reservationDatetime) els.reservationDatetime.value = '';
    state.seats = 2; els.seatCount.textContent = 2;
    setTimeout(loadAvailability, 1000);
  } catch (err) { showToast(err.message, 'error'); }
  finally {
    els.submitBtn.disabled = false;
    els.submitBtn.querySelector('.submit-text').textContent = 'Platz reservieren';
  }
});

const RING_CIRCUMFERENCE = 2 * Math.PI * 44;

function startCountdown(reservationDatetime = null) {
  clearInterval(state.countdownInt);

  if (reservationDatetime) {
    // Vorausreservierung: Countdown bis zur Ankunftszeit + 15 min
    const expiresAt = new Date(new Date(reservationDatetime).getTime() + 15 * 60 * 1000);
    function tick() {
      const remaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      state.countdownSec = remaining;
      updateCountdown();
      if (remaining <= 0) {
        clearInterval(state.countdownInt);
        showToast('Reservierung abgelaufen!', 'error');
        closeModal(els.successModal);
        loadAvailability();
      }
    }
    tick();
    state.countdownInt = setInterval(tick, 1000);
  } else {
    // Sofortreservierung: 15 Minuten ab jetzt
    state.countdownSec = 15 * 60;
    updateCountdown();
    state.countdownInt = setInterval(() => {
      state.countdownSec--;
      updateCountdown();
      if (state.countdownSec <= 0) {
        clearInterval(state.countdownInt);
        showToast('Reservierung abgelaufen!', 'error');
        closeModal(els.successModal);
        loadAvailability();
      }
    }, 1000);
  }
}

function updateCountdown() {
  const sec = state.countdownSec;
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  els.countdownTime.textContent = `${m}:${s}`;
  const totalSec = 15 * 60;
  const offset = RING_CIRCUMFERENCE * (1 - Math.min(sec, totalSec) / totalSec);
  els.ringProgress.style.strokeDashoffset = offset;
  if (sec <= 120) {
    els.ringProgress.style.stroke = 'var(--red)';
    els.countdownTime.style.color = 'var(--red)';
  }
}

function openModal(overlay)  { overlay.classList.add('open');    document.body.style.overflow = 'hidden'; }
function closeModal(overlay) { overlay.classList.remove('open'); document.body.style.overflow = ''; }

[els.successModal, els.gameModal, els.adminModal, els.authModal, els.checkInModal].forEach(overlay => {
  if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(overlay); });
});
els.modalClose.addEventListener('click', () => { clearInterval(state.countdownInt); closeModal(els.successModal); });
els.gameModalClose.addEventListener('click', () => { stopGame(); closeModal(els.gameModal); });
els.adminModalClose.addEventListener('click', () => closeModal(els.adminModal));
if (els.checkInModalClose) els.checkInModalClose.addEventListener('click', () => closeModal(els.checkInModal));

els.gameBtn.addEventListener('click', () => { openModal(els.gameModal); startGame(); });
function startGame() {
  const canvas = els.gameCanvas;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  let ballX = W/2, ballY = 30, ballVX = 2, ballVY = 2;
  let paddleX = W/2 - 40;
  const paddleW = 80, paddleH = 8;
  let score = 0, frame = 0;
  canvas.addEventListener('mousemove', e => { const r = canvas.getBoundingClientRect(); paddleX = (e.clientX - r.left) - paddleW/2; });
  canvas.addEventListener('touchmove', e => { e.preventDefault(); const r = canvas.getBoundingClientRect(); paddleX = (e.touches[0].clientX - r.left) - paddleW/2; }, { passive: false });
  function draw() {
    frame++;
    ctx.clearRect(0, 0, W, H); ctx.fillStyle = '#111111'; ctx.fillRect(0, 0, W, H);
    ballX += ballVX; ballY += ballVY;
    if (ballX < 12 || ballX > W-12) ballVX *= -1;
    if (ballY < 12) ballVY *= -1;
    if (ballY > H-paddleH-20 && ballY < H-10 && ballX > paddleX && ballX < paddleX+paddleW) {
      ballVY = -Math.abs(ballVY); score++;
      ballVX += (Math.random()-0.5)*0.5;
      if (Math.abs(ballVX) > 5) ballVX = Math.sign(ballVX)*5;
    }
    if (ballY > H+20) { ballX = W/2; ballY = 30; ballVX = (Math.random()>0.5?1:-1)*2; ballVY = 2; }
    ctx.font = '20px serif'; ctx.textAlign = 'center'; ctx.fillText('🍺', ballX, ballY);
    ctx.fillStyle = '#c9a84c'; ctx.beginPath(); ctx.roundRect(paddleX, H-paddleH-16, paddleW, paddleH, 4); ctx.fill();
    ctx.fillStyle = 'rgba(201,168,76,0.8)'; ctx.font = '500 14px "DM Mono",monospace'; ctx.textAlign = 'left'; ctx.fillText(`Score: ${score}`, 12, 22);
    if (frame < 120) { ctx.fillStyle = 'rgba(240,237,232,0.3)'; ctx.font = '12px "DM Sans",sans-serif'; ctx.textAlign = 'center'; ctx.fillText('Bewege die Maus / tippe', W/2, H/2); }
    state.gameLoop = requestAnimationFrame(draw);
  }
  draw();
}
function stopGame() { if (state.gameLoop) { cancelAnimationFrame(state.gameLoop); state.gameLoop = null; } }

els.adminBtn.addEventListener('click', () => openModal(els.adminModal));
els.adminLoginBtn.addEventListener('click', async () => {
  const username = els.adminUser.value.trim();
  const password = els.adminPass.value.trim();
  if (!username || !password) { els.adminStatus.textContent = 'Bitte alle Felder ausfüllen.'; return; }
  els.adminLoginBtn.disabled = true;
  els.adminStatus.textContent = 'Wird eingeloggt…';
  try {
    const data = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
    state.token = data.access_token;
    els.adminStatus.textContent = '✓ Eingeloggt!';
    els.adminStatus.style.color = 'var(--green)';
    setTimeout(() => { closeModal(els.adminModal); showToast('Admin: ' + username, 'success'); els.adminStatus.textContent = ''; els.adminStatus.style.color = ''; }, 800);
  } catch (err) { els.adminStatus.textContent = err.message; els.adminStatus.style.color = 'var(--red)'; }
  finally { els.adminLoginBtn.disabled = false; }
});

els.refreshBtn.addEventListener('click', loadAvailability);

// ══════════════════════════════════════════════════════════════
// MEINE RESERVIERUNGEN
// ══════════════════════════════════════════════════════════════

async function loadMyReservations() {
  if (!state.token) return;
  try {
    const reservations = await apiFetch('/reservations/my');
    renderMyReservations(reservations);
  } catch {
    renderMyReservations([]);
  }
}

function renderMyReservations(reservations) {
  const section = els.myReservationsSection;
  const list    = els.myReservationsList;

  if (!reservations.length) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';

  const statusLabel = {
    PENDING:    { text: 'Aktiv',       color: 'var(--gold)' },
    CHECKED_IN: { text: 'Eingecheckt', color: 'var(--green)' },
    EXPIRED:    { text: 'Abgelaufen',  color: 'var(--text-muted)' },
    CANCELLED:  { text: 'Storniert',   color: 'var(--red)' },
  };

  list.innerHTML = reservations.map(r => {
    const s         = statusLabel[r.status] || { text: r.status, color: 'var(--text-muted)' };
    const isPending = r.status === 'PENDING';

    // Zeige Ankunftszeit wenn vorhanden, sonst Reservierungszeitpunkt
    const displayDt = r.reservation_datetime
      ? new Date(r.reservation_datetime)
      : new Date(r.reserved_at);
    const date = displayDt.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
    const time = displayDt.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    const label = r.reservation_datetime ? 'Ankunft' : 'Reserviert';

    return `
      <div class="my-res-item ${isPending ? 'my-res-active' : ''}">
        <div class="my-res-top">
          <span class="my-res-code">${r.confirmation_code}</span>
          <span class="my-res-status" style="color:${s.color}">${s.text}</span>
        </div>
        <div class="my-res-meta">
          <span>${r.guest_name} · ${r.seats_reserved} ${r.seats_reserved === 1 ? 'Person' : 'Personen'}</span>
          <span>${label}: ${date}, ${time}</span>
        </div>
        ${isPending ? `
          <div class="my-res-actions">
            <button class="my-res-show-btn" onclick="showCodeModal('${r.confirmation_code}')">
              Code anzeigen
            </button>
            <button class="my-res-cancel-btn" onclick="cancelReservation(${r.id})">
              Stornieren
            </button>
          </div>` : ''}
      </div>`;
  }).join('');
}

function showCodeModal(code) {
  els.confirmCode.textContent = code;
  openModal(els.successModal);
}

async function cancelReservation(reservationId) {
  if (!confirm('Reservierung wirklich stornieren?')) return;
  try {
    await apiFetch(`/reservations/${reservationId}`, { method: 'DELETE' });
    showToast('Reservierung storniert ✓', 'success');
    loadMyReservations();
    loadAvailability();
    els.menuSection.style.display = 'none';
  } catch (err) {
    showToast(err.message, 'error');
  }
}

if (els.myResBtn) {
  els.myResBtn.addEventListener('click', loadMyReservations);
}

// ══════════════════════════════════════════════════════════════
// CHECK-IN
// ══════════════════════════════════════════════════════════════

function openCheckIn() {
  if (els.checkInModal) {
    els.checkInInput.value = '';
    els.checkInStatus.textContent = '';
    els.checkInStatus.style.color = '';
    openModal(els.checkInModal);
  }
}

if (els.checkInBtn) {
  els.checkInBtn.addEventListener('click', async () => {
    const code = els.checkInInput.value.trim().toUpperCase();
    if (!code) {
      els.checkInStatus.textContent = 'Bitte Code eingeben.';
      els.checkInStatus.style.color = 'var(--red)';
      return;
    }
    els.checkInBtn.disabled = true;
    els.checkInStatus.textContent = 'Wird eingecheckt…';
    els.checkInStatus.style.color = 'var(--text-muted)';
    try {
      await apiFetch('/reservations/check-in', {
        method: 'POST',
        body: JSON.stringify({ confirmation_code: code }),
      });
      els.checkInStatus.textContent = '✓ Eingecheckt!';
      els.checkInStatus.style.color = 'var(--green)';
      showToast('Gast erfolgreich eingecheckt! 🍺', 'success');
      setTimeout(() => {
        closeModal(els.checkInModal);
        loadMyReservations();
        loadAvailability();
      }, 1200);
    } catch (err) {
      els.checkInStatus.textContent = err.message;
      els.checkInStatus.style.color = 'var(--red)';
    } finally {
      els.checkInBtn.disabled = false;
    }
  });
}

if (els.checkInInput) {
  els.checkInInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') els.checkInBtn.click();
  });
}

// ══════════════════════════════════════════════════════════════
// MENU & ORDER
// ══════════════════════════════════════════════════════════════

function showMenuSection() {
  els.menuSection.style.display = 'block';
  setTimeout(() => {
    els.menuSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 400);
  loadMenu();
}

async function loadMenu() {
  els.menuCategories.innerHTML = `<div class="menu-loading"><span class="menu-loading-dot"></span><span class="menu-loading-dot"></span><span class="menu-loading-dot"></span></div>`;
  try {
    const data = await apiFetch('/menu');
    let categories = [];
    if (Array.isArray(data)) {
      categories = data;
    } else if (data.food || data.beverages) {
      categories = [...(data.food || []), ...(data.beverages || [])];
    } else {
      categories = data.categories || [];
    }
    renderMenu(categories);
  } catch {
    els.menuCategories.innerHTML = `<p style="color:var(--text-muted);font-size:13px;text-align:center;padding:20px">Menü konnte nicht geladen werden.</p>`;
  }
}

function renderMenu(categories) {
  if (!categories.length) {
    els.menuCategories.innerHTML = `<p style="color:var(--text-muted);font-size:13px;text-align:center;padding:20px">Keine Einträge verfügbar.</p>`;
    return;
  }
  els.menuCategories.innerHTML = categories.map(cat => {
    const catName = cat.name || cat.category || 'Sonstiges';
    const items   = cat.items || [];
    return `
    <div class="menu-category">
      <h3 class="menu-cat-title">${catName}</h3>
      <div class="menu-items-list">
        ${items.map(item => `
          <div class="menu-item">
            <div class="menu-item-info">
              <span class="menu-item-name">${item.name}</span>
              ${item.description ? `<span class="menu-item-desc">${item.description}</span>` : ''}
            </div>
            <div class="menu-item-right">
              <span class="menu-item-price">${formatPrice(item.price)}</span>
              <div class="menu-item-qty">
                <button class="qty-btn qty-minus" data-id="${item.id}" data-price="${item.price}" data-name="${item.name}">−</button>
                <span class="qty-count" id="qty-${item.id}">0</span>
                <button class="qty-btn qty-plus"  data-id="${item.id}" data-price="${item.price}" data-name="${item.name}">+</button>
              </div>
            </div>
          </div>`).join('')}
      </div>
    </div>`;
  }).join('');

  els.menuCategories.addEventListener('click', e => {
    const btn = e.target.closest('.qty-btn');
    if (!btn) return;
    const id = btn.dataset.id, price = parseFloat(btn.dataset.price), name = btn.dataset.name;
    if (btn.classList.contains('qty-plus')) {
      if (!state.cart[id]) state.cart[id] = { name, price, qty: 0 };
      state.cart[id].qty++;
    } else {
      if (state.cart[id]?.qty > 0) { state.cart[id].qty--; if (state.cart[id].qty === 0) delete state.cart[id]; }
    }
    const qtyEl = $(`qty-${id}`);
    if (qtyEl) qtyEl.textContent = state.cart[id]?.qty ?? 0;
    renderCart();
  });
}

function renderCart() {
  const items = Object.entries(state.cart).filter(([, v]) => v.qty > 0);
  if (!items.length) { els.cartWrap.style.display = 'none'; return; }
  els.cartWrap.style.display = 'block';
  let total = 0;
  els.cartItems.innerHTML = items.map(([, { name, price, qty }]) => {
    const line = price * qty; total += line;
    return `<div class="cart-item"><span class="cart-item-qty">${qty}×</span><span class="cart-item-name">${name}</span><span class="cart-item-price">${formatPrice(line)}</span></div>`;
  }).join('');
  els.cartCount.textContent = `${items.reduce((s,[,v])=>s+v.qty,0)} Artikel`;
  els.cartTotal.textContent = formatPrice(total);
}

els.orderSubmitBtn.addEventListener('click', async () => {
  if (!state.reservationId) { showToast('Keine aktive Reservierung', 'error'); return; }
  const items = Object.entries(state.cart).filter(([,v])=>v.qty>0).map(([id,{qty}])=>({menu_item_id:parseInt(id),quantity:qty}));
  if (!items.length) { showToast('Warenkorb ist leer', 'error'); return; }
  els.orderSubmitBtn.disabled = true;
  els.orderSubmitBtn.querySelector('.submit-text').textContent = 'Wird gesendet…';
  try {
    const order = await apiFetch(`/orders/reservations/${state.reservationId}`, { method: 'POST', body: JSON.stringify({ items }) });
    state.cart = {};
    document.querySelectorAll('.qty-count').forEach(el => el.textContent = '0');
    renderCart();
    showOrderConfirmation(order);
    showToast('Vorbestellung gespeichert! 🍺', 'success');
  } catch (err) { showToast(err.message, 'error'); }
  finally { els.orderSubmitBtn.disabled = false; els.orderSubmitBtn.querySelector('.submit-text').textContent = 'Vorbestellung absenden'; }
});

async function loadExistingOrder(reservationId) {
  if (!reservationId) return;
  try {
    const order = await apiFetch(`/orders/reservations/${reservationId}`);
    if (order?.items?.length) showOrderConfirmation(order);
  } catch { /* keine Bestellung vorhanden */ }
}

function showOrderConfirmation(order) {
  els.cartWrap.style.display = 'none';
  els.orderConfirmation.style.display = 'block';
  els.orderConfItems.innerHTML = order.items.map(i =>
    `<div class="cart-item"><span class="cart-item-qty">${i.quantity}×</span><span class="cart-item-name">${i.item_name ?? 'Artikel'}</span><span class="cart-item-price">${formatPrice((i.unit_price??0)*i.quantity)}</span></div>`
  ).join('');
}

els.orderEditBtn.addEventListener('click', () => {
  els.orderConfirmation.style.display = 'none';
  state.cart = {};
  document.querySelectorAll('.qty-count').forEach(el => el.textContent = '0');
  renderCart();
});

function formatPrice(amount) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amount);
}

// ── INIT ───────────────────────────────────────────────────────
loadAvailability();