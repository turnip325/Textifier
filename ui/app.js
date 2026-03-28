// app.js — Frontend logic for Textifier.
// Manages the LED state machine, Execute/Purge button behaviour,
// and communication with the Python HTTP backend.

'use strict';

// ---------------------------------------------------------------- Elements
const led        = document.getElementById('led');
const lcd        = document.getElementById('lcd');
const input      = document.getElementById('filename-input');
const btnExec    = document.getElementById('btn-execute');
const btnPurge   = document.getElementById('btn-purge');
const imgCount   = document.getElementById('img-count');

// ---------------------------------------------------------- LED state machine
// States: 'off' | 'idle' | 'working' | 'success' | 'error' | 'purge-confirm'
function setLed(state) {
  led.className = 'led';   // clear all state classes
  if (state !== 'off') led.classList.add(state);
}

// ------------------------------------------------------------------ LCD log
function setLcd(msg, isError = false) {
  lcd.textContent = msg;
  lcd.className   = isError ? 'lcd lcd-error' : 'lcd lcd-ok';
}

// ----------------------------------------------------- Image count badge
async function refreshCount() {
  try {
    const res  = await fetch('/status');
    const data = await res.json();
    const n    = data.image_count ?? 0;
    imgCount.textContent = n === 1 ? '1 image ready' : `${n} images ready`;
  } catch {
    imgCount.textContent = '? images';
  }
}

// ----------------------------------------------------------------- Execute
btnExec.addEventListener('click', async () => {
  const filename = input.value.trim();

  if (!filename) {
    setLcd('Enter an output filename first.', true);
    setLed('error');
    input.focus();
    setTimeout(() => setLed('idle'), 2000);
    return;
  }

  // Guard: no path separators (extra safety on top of server-side sanitisation)
  if (filename.includes('/') || filename.includes('\\')) {
    setLcd('Filename cannot contain path separators.', true);
    setLed('error');
    setTimeout(() => setLed('idle'), 2000);
    return;
  }

  // Lock UI during processing
  btnExec.disabled = true;
  btnPurge.disabled = true;
  setLed('working');
  setLcd('Processing images…');

  try {
    const res  = await fetch('/execute', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ filename })
    });
    const data = await res.json();

    if (data.ok) {
      const pages = data.pages === 1 ? '1 page' : `${data.pages} pages`;
      setLcd(`${pages} processed → ${data.output}`);
      setLed('success');
    } else {
      setLcd(data.error || 'Unknown error.', true);
      setLed('error');
    }
  } catch (err) {
    setLcd('Connection error — is the server running?', true);
    setLed('error');
  }

  // Re-enable after a short visual pause so the user sees the result LED
  setTimeout(() => {
    btnExec.disabled  = false;
    btnPurge.disabled = false;
    setLed('idle');
    refreshCount();
  }, 2500);
});

// ------------------------------------------------------------------ Purge
// Two-click confirmation pattern:
//   First click  → button shows "CONFIRM?", LED pulses, 3-second window opens
//   Second click → fires /purge
//   Timeout      → reverts to normal without action

let purgeTimer   = null;
let purgeArmed   = false;

function armPurge() {
  purgeArmed = true;
  btnPurge.textContent = 'CONFIRM?';
  btnPurge.classList.add('confirming');
  setLed('purge-confirm');

  purgeTimer = setTimeout(disarmPurge, 3000);
}

function disarmPurge() {
  purgeArmed = false;
  clearTimeout(purgeTimer);
  btnPurge.textContent = 'PURGE';
  btnPurge.classList.remove('confirming');
  setLed('idle');
}

btnPurge.addEventListener('click', async () => {
  if (!purgeArmed) {
    armPurge();
    return;
  }

  // Second click — confirmed
  clearTimeout(purgeTimer);
  disarmPurge();

  btnExec.disabled  = true;
  btnPurge.disabled = true;
  setLed('working');
  setLcd('Clearing ~/Source…');

  try {
    const res  = await fetch('/purge', { method: 'POST' });
    const data = await res.json();

    if (data.ok) {
      const n = data.deleted;
      setLcd(`Source cleared — ${n} ${n === 1 ? 'file' : 'files'} removed`);
      setLed('success');
    } else {
      setLcd(data.error || 'Purge failed.', true);
      setLed('error');
    }
  } catch (err) {
    setLcd('Connection error during purge.', true);
    setLed('error');
  }

  setTimeout(() => {
    btnExec.disabled  = false;
    btnPurge.disabled = false;
    setLed('idle');
    refreshCount();
  }, 2000);
});

// -------------------------------------------- Disarm purge if user clicks elsewhere
document.addEventListener('click', (e) => {
  if (purgeArmed && e.target !== btnPurge) {
    disarmPurge();
  }
});

// ------------------------------------------ Initialise on page load
(async () => {
  setLed('idle');
  await refreshCount();
})();
