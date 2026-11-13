/**
 * chat.js — Chat interface logic
 */

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const clearChatBtn = document.getElementById('clearChatBtn');

// ── Auto-resize textarea ────────────────────────────────────────────────────
chatInput?.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

// ── Enter key handling ──────────────────────────────────────────────────────
chatInput?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn?.addEventListener('click', sendMessage);
clearChatBtn?.addEventListener('click', clearChat);

// ── Send message ────────────────────────────────────────────────────────────
async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  // Disable inputs
  sendBtn.disabled = true;
  chatInput.disabled = true;
  chatInput.value = '';
  chatInput.style.height = 'auto';

  // Append user bubble
  appendMessage('user', message);
  scrollToBottom();

  // Show typing indicator
  typingIndicator.style.display = 'flex';
  scrollToBottom();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    typingIndicator.style.display = 'none';
    appendMessage('assistant', data.reply || 'Sorry, I could not generate a response.');
  } catch (err) {
    typingIndicator.style.display = 'none';
    appendMessage('assistant', '❌ Error connecting to the AI service. Please check your IBM API credentials and try again.');
    showToast('Connection error. Check your .env configuration.', 'danger');
  } finally {
    sendBtn.disabled = false;
    chatInput.disabled = false;
    chatInput.focus();
    scrollToBottom();
  }
}

// ── Append a message bubble ─────────────────────────────────────────────────
function appendMessage(role, content) {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const el = document.createElement('div');

  if (role === 'user') {
    el.className = 'chat-msg user-msg';
    el.innerHTML = `
      <div class="msg-bubble">
        <div class="msg-text">${escapeHtml(content)}</div>
        <div class="msg-time">${now}</div>
      </div>
      <div class="msg-avatar user-avatar"><i class="bi bi-person-fill"></i></div>`;
  } else {
    el.className = 'chat-msg assistant-msg';
    el.innerHTML = `
      <div class="msg-avatar assistant-avatar"><i class="bi bi-robot"></i></div>
      <div class="msg-bubble">
        <div class="msg-text">${formatAIText(content)}</div>
        <div class="msg-time">${now}</div>
      </div>`;
  }

  chatMessages.appendChild(el);
}

// ── Clear conversation ──────────────────────────────────────────────────────
async function clearChat() {
  if (!confirm('Clear the entire conversation?')) return;
  try {
    await fetch('/api/chat/clear', { method: 'POST' });
    // Keep only the welcome message
    const msgs = chatMessages.querySelectorAll('.chat-msg');
    msgs.forEach((m, i) => { if (i > 0) m.remove(); });
    showToast('Conversation cleared.', 'success');
  } catch {
    showToast('Failed to clear conversation.', 'danger');
  }
}

// ── Suggestion chips ────────────────────────────────────────────────────────
function injectSuggestion(btn) {
  chatInput.value = btn.textContent.trim();
  chatInput.focus();
  chatInput.dispatchEvent(new Event('input'));
}
window.injectSuggestion = injectSuggestion;

// ── Utilities ───────────────────────────────────────────────────────────────
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Scroll to bottom on load (for existing history)
scrollToBottom();
