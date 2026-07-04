/**
 * main.js — Core utilities: sidebar, dark mode, toasts, AI text formatter
 */

// ── Dark / Light Mode ──────────────────────────────────────────────────────
const root = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

function applyTheme(theme) {
  root.setAttribute('data-theme', theme);
  themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
  localStorage.setItem('vgr_theme', theme);
}

// Restore saved theme
applyTheme(localStorage.getItem('vgr_theme') || 'light');

themeToggle?.addEventListener('click', () => {
  applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
});

// ── Sidebar Toggle ─────────────────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');
const sidebarToggle = document.getElementById('sidebarToggle');

// Inject overlay element
const overlay = document.createElement('div');
overlay.className = 'sidebar-overlay';
document.body.appendChild(overlay);

function closeSidebar() {
  sidebar?.classList.remove('open');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

function openSidebar() {
  if (window.innerWidth <= 992) {
    sidebar?.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

sidebarToggle?.addEventListener('click', () => {
  if (window.innerWidth <= 992) {
    const isOpen = sidebar?.classList.contains('open');
    if (isOpen) {
      closeSidebar();
    } else {
      openSidebar();
    }
  } else {
    // On desktop: collapse/expand
    const collapsed = sidebar.style.width === '60px';
    sidebar.style.width = collapsed ? 'var(--sidebar-width)' : '60px';
    mainContent.style.marginLeft = collapsed ? 'var(--sidebar-width)' : '60px';
  }
});

overlay.addEventListener('click', closeSidebar);
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeSidebar();
});
window.addEventListener('resize', () => {
  if (window.innerWidth > 992) {
    closeSidebar();
  }
});

// ── Toast Notifications ────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const colors = {
    success: '#059669',
    danger: '#dc2626',
    warning: '#d97706',
    info: '#0891b2',
    primary: '#1a56db',
  };

  const icons = {
    success: 'bi-check-circle-fill',
    danger: 'bi-exclamation-triangle-fill',
    warning: 'bi-exclamation-circle-fill',
    info: 'bi-info-circle-fill',
    primary: 'bi-info-circle-fill',
  };

  const id = `toast_${Date.now()}`;
  const el = document.createElement('div');
  el.id = id;
  el.className = 'toast show align-items-center';
  el.setAttribute('role', 'alert');
  el.innerHTML = `
    <div class="d-flex align-items-center gap-2 p-3">
      <i class="bi ${icons[type] || icons.info}" style="color:${colors[type] || colors.info};font-size:16px;"></i>
      <span style="font-size:13px;">${message}</span>
      <button type="button" class="btn-close ms-auto" onclick="document.getElementById('${id}').remove()"></button>
    </div>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── AI Text Formatter ──────────────────────────────────────────────────────
/**
 * Converts plain AI output into readable HTML.
 * Handles: **bold**, *italic*, ## headers, - bullet lists, numbered lists.
 */
function formatAIText(text) {
  if (!text) return '';
  let html = text
    // Escape HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers: ## or ###
    .replace(/^###\s+(.+)$/gm, '<h4 class="mt-3 mb-1" style="color:var(--primary);font-size:14px;font-weight:700">$1</h4>')
    .replace(/^##\s+(.+)$/gm, '<h3 class="mt-3 mb-2" style="color:var(--primary);font-size:15px;font-weight:700">$1</h3>')
    .replace(/^#\s+(.+)$/gm, '<h2 class="mt-3 mb-2" style="color:var(--primary);font-size:16px;font-weight:700">$1</h2>')
    // Bold & italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Bullet lines
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    // Numbered list
    .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> items
    .replace(/((<li>.*<\/li>\n?)+)/g, '<ul class="ms-3 mb-2">$1</ul>')
    // Horizontal rule
    .replace(/^---+$/gm, '<hr/>')
    // Line breaks
    .replace(/\n\n+/g, '</p><p class="mb-2">')
    .replace(/\n/g, '<br/>');

  return `<p class="mb-2">${html}</p>`;
}

// Expose globally
window.formatAIText = formatAIText;
window.showToast = showToast;

// ── User Dropdown Menu ─────────────────────────────────────────────────────
const userDropdownBtn = document.getElementById('userDropdownBtn');
const userDropdownMenu = document.getElementById('userDropdownMenu');
const userDropdownWrap = document.getElementById('userDropdownWrap');

if (userDropdownBtn && userDropdownMenu) {
  // Toggle on button click
  userDropdownBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = userDropdownMenu.classList.contains('show');
    userDropdownMenu.classList.toggle('show');
    userDropdownBtn.setAttribute('aria-expanded', !isOpen);
  });

  // Close on menu item click
  document.querySelectorAll('.topbar-dd-item').forEach(item => {
    item.addEventListener('click', () => {
      userDropdownMenu.classList.remove('show');
      userDropdownBtn.setAttribute('aria-expanded', false);
    });
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!userDropdownWrap?.contains(e.target)) {
      userDropdownMenu.classList.remove('show');
      userDropdownBtn.setAttribute('aria-expanded', false);
    }
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      userDropdownMenu.classList.remove('show');
      userDropdownBtn.setAttribute('aria-expanded', false);
    }
  });
}
