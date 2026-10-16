/**
 * Campus Hostel LAN – Main JavaScript
 */

// ── Live clock ─────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('topbarTime');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' });
}
updateClock();
setInterval(updateClock, 1000);

// ── Sidebar toggle (mobile) ────────────────────────────────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.toggle('open');
}

// ── Close modal when clicking outside ─────────────────────────
function toggleModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.toggle('hidden');
}
function closeModalOutside(event, id) {
  if (event.target.id === id) {
    document.getElementById(id).classList.add('hidden');
  }
}
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden'));
  }
});

// ── Table search filter ─────────────────────────────────────────
function filterTable(input) {
  const filter = input.value.toLowerCase();
  const table  = document.getElementById('studentsTable');
  if (!table) return;
  const rows = table.querySelectorAll('tbody tr');
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(filter) ? '' : 'none';
  });
}

// ── Auto-dismiss flash messages ────────────────────────────────
document.querySelectorAll('.flash').forEach(flash => {
  setTimeout(() => {
    flash.style.opacity = '0';
    flash.style.transform = 'translateY(-10px)';
    flash.style.transition = '0.4s ease';
    setTimeout(() => flash.remove(), 400);
  }, 4000);
});

// ── Animate stat values ────────────────────────────────────────
function animateCount(el) {
  const target = parseInt(el.textContent.replace(/\D/g,''), 10);
  if (isNaN(target) || target === 0) return;
  let current = 0;
  const step = Math.ceil(target / 25);
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current >= target) clearInterval(timer);
  }, 30);
}

document.querySelectorAll('.stat-value').forEach(el => {
  if (/^\d+$/.test(el.textContent.trim())) {
    animateCount(el);
  }
});

// ── Occupancy bar animation ────────────────────────────────────
document.querySelectorAll('.occ-bar').forEach(bar => {
  const target = bar.style.width;
  bar.style.width = '0%';
  setTimeout(() => {
    bar.style.transition = 'width 0.8s cubic-bezier(0.4,0,0.2,1)';
    bar.style.width = target;
  }, 200);
});

// ── Sidebar active link scroll into view ─────────────────────
document.querySelectorAll('.nav-item.active').forEach(el => {
  el.scrollIntoView({ block: 'nearest' });
});
