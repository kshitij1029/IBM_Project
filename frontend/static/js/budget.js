/**
 * budget.js — Budget Planner page logic
 */

// ── Style radio feedback ──────────────────────────────────────────────────────
document.querySelectorAll('input[name="budgetStyle"]').forEach(radio => {
  radio.addEventListener('change', () => {
    document.querySelectorAll('.style-option').forEach(opt => opt.classList.remove('checked'));
    radio.closest('.style-option').classList.add('checked');
  });
});

// ── Chart instances ───────────────────────────────────────────────────────────
let pieChartInstance = null;
let expenseChartInstance = null;

// ── Manual expense tracker ────────────────────────────────────────────────────
const expenses = {};

document.getElementById('addExpenseBtn')?.addEventListener('click', () => {
  const cat = document.getElementById('expenseCategory').value;
  const amt = parseFloat(document.getElementById('expenseAmount').value);
  if (!amt || amt <= 0) { showToast('Enter a valid amount.', 'warning'); return; }

  expenses[cat] = (expenses[cat] || 0) + amt;
  document.getElementById('expenseAmount').value = '';
  renderExpenseList();
  updateExpenseChart();
  showToast(`Added ₹${formatNum(amt)} to ${cat}.`, 'success');
});

function renderExpenseList() {
  const container = document.getElementById('expenseList');
  container.innerHTML = '';
  let total = 0;
  Object.entries(expenses).forEach(([cat, amt]) => {
    total += amt;
    const item = document.createElement('div');
    item.className = 'expense-item';
    item.innerHTML = `
      <span>${cat}</span>
      <span class="fw-semibold text-success">₹${formatNum(amt)}</span>
      <button class="btn-icon-sm text-danger ms-2" onclick="removeExpense('${cat}')">
        <i class="bi bi-x"></i>
      </button>`;
    container.appendChild(item);
  });
  document.getElementById('totalSpent').textContent = `₹${formatNum(total)}`;
}

window.removeExpense = (cat) => {
  delete expenses[cat];
  renderExpenseList();
  updateExpenseChart();
};

function updateExpenseChart() {
  const keys = Object.keys(expenses);
  if (keys.length === 0) {
    document.getElementById('expenseChartCard').style.display = 'none';
    return;
  }

  document.getElementById('expenseChartCard').style.display = 'block';
  const ctx = document.getElementById('expenseChart').getContext('2d');
  if (expenseChartInstance) expenseChartInstance.destroy();

  expenseChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: keys,
      datasets: [{
        label: 'Expense (₹)',
        data: keys.map(k => expenses[k]),
        backgroundColor: ['#1a56db','#7c3aed','#059669','#d97706','#ef4444','#0891b2'],
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ₹${formatNum(ctx.parsed.y)}` } },
      },
      scales: {
        y: {
          ticks: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim(),
            callback: v => `₹${formatNum(v)}`,
          },
          grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--border').trim() },
        },
        x: {
          ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() },
          grid: { display: false },
        },
      },
    },
  });
}

// ── Calculate Budget (instant) ───────────────────────────────────────────────
document.getElementById('calcBudgetBtn')?.addEventListener('click', async () => {
  const payload = {
    duration_days: parseInt(document.getElementById('budgetDays').value) || 5,
    travelers: parseInt(document.getElementById('budgetTravelers').value) || 1,
    travel_style: document.querySelector('input[name="budgetStyle"]:checked')?.value || 'mid-range',
    is_international: document.getElementById('budgetIntl').checked,
  };

  try {
    const res = await fetch('/api/budget/estimate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    renderBudgetBreakdown(data);
    document.getElementById('budgetPlaceholder').style.display = 'none';
  } catch {
    showToast('Budget calculation failed.', 'danger');
  }
});

// ── AI Detailed Budget ───────────────────────────────────────────────────────
document.getElementById('aiBudgetBtn')?.addEventListener('click', async () => {
  const destination = document.getElementById('budgetDest').value.trim();
  if (!destination) { showToast('Enter a destination for AI estimate.', 'warning'); return; }

  const btn = document.getElementById('aiBudgetBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing…';

  const aiBudgetResult = document.getElementById('aiBudgetResult');
  aiBudgetResult.style.display = 'block';
  document.getElementById('aiBudgetText').innerHTML =
    '<div class="text-center py-3"><div class="spinner-border text-warning"></div><p class="mt-2 text-muted">AI is analyzing costs for ' + destination + '…</p></div>';
  document.getElementById('budgetPlaceholder').style.display = 'none';

  try {
    const res = await fetch('/api/budget/ai-estimate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination,
        duration_days: parseInt(document.getElementById('budgetDays').value) || 5,
        travelers: parseInt(document.getElementById('budgetTravelers').value) || 1,
        travel_style: document.querySelector('input[name="budgetStyle"]:checked')?.value || 'mid-range',
        traveler_type: 'solo',
      }),
    });
    const data = await res.json();
    document.getElementById('aiBudgetText').innerHTML = formatAIText(data.estimate || data.error);
    showToast('AI budget analysis ready!', 'success');
  } catch {
    document.getElementById('aiBudgetText').innerHTML = '<p class="text-danger">AI estimate failed. Check service connection.</p>';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-magic me-2"></i>AI Detailed Estimate';
  }
});

// ── Render Budget Breakdown ──────────────────────────────────────────────────
function renderBudgetBreakdown(bb) {
  const categories = ['accommodation','transport','food','sightseeing','shopping','miscellaneous'];
  const labels = ['Accommodation','Transport','Food','Sightseeing','Shopping','Misc'];
  const colors = ['#1a56db','#7c3aed','#059669','#d97706','#ef4444','#0891b2'];

  // Read CSS variables at render time so colors adapt to the active theme
  const cs = getComputedStyle(document.documentElement);
  const themeColors = [
    cs.getPropertyValue('--primary').trim()  || colors[0],
    '#7c3aed',
    cs.getPropertyValue('--success').trim()  || colors[2],
    cs.getPropertyValue('--warning').trim()  || colors[3],
    cs.getPropertyValue('--danger').trim()   || colors[4],
    cs.getPropertyValue('--info').trim()     || colors[5],
  ];

  const container = document.getElementById('budgetStatCards');
  container.innerHTML = '';
  categories.forEach((cat, i) => {
    const div = document.createElement('div');
    div.className = 'col-6 col-sm-4';
    div.innerHTML = `
      <div class="budget-stat-card">
        <div class="budget-stat-label">${labels[i]}</div>
        <div class="budget-stat-value" style="color:${themeColors[i]}">₹${formatNum(bb[cat])}</div>
      </div>`;
    container.appendChild(div);
  });

  document.getElementById('totalBudgetDisplay').textContent = `Estimated Total: ₹${formatNum(bb.total)}`;
  document.getElementById('budgetBreakdownCard').style.display = 'block';

  // Pie chart
  if (pieChartInstance) pieChartInstance.destroy();
  const ctx = document.getElementById('budgetPieChart').getContext('2d');
  pieChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: categories.map(c => bb[c]),
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#fff',
      }],
    },
    options: {
      responsive: true,
      cutout: '55%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim(),
            font: { size: 12 },
            padding: 12,
          },
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ₹${formatNum(ctx.parsed)} (${((ctx.parsed / bb.total) * 100).toFixed(1)}%)`,
          },
        },
      },
    },
  });
}

function formatNum(n) {
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}
