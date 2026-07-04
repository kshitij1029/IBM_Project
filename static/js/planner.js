/**
 * planner.js — Trip Planner page logic
 */

// ── Interest tags ────────────────────────────────────────────────────────────
document.querySelectorAll('#interestTags .interest-tag').forEach(tag => {
  tag.addEventListener('click', () => tag.classList.toggle('selected'));
});

// ── Travel Style radio visual feedback ──────────────────────────────────────
document.querySelectorAll('input[name="travelStyle"]').forEach(radio => {
  radio.addEventListener('change', () => {
    document.querySelectorAll('.style-option').forEach(opt => opt.classList.remove('checked'));
    radio.closest('.style-option').classList.add('checked');
  });
});

// ── Show family panel when traveler type is "family" ─────────────────────────
document.getElementById('travelerType')?.addEventListener('change', function() {
  const panel = document.getElementById('familyPanel');
  panel.style.display = this.value === 'family' ? 'block' : 'none';
});

// ── Pre-fill destination from URL param ──────────────────────────────────────
const urlParams = new URLSearchParams(window.location.search);
const destParam = urlParams.get('dest');
if (destParam) {
  const destInput = document.getElementById('destination');
  if (destInput) destInput.value = destParam;
}

// ── Date sync ────────────────────────────────────────────────────────────────
document.getElementById('startDate')?.addEventListener('change', function() {
  const days = parseInt(document.getElementById('durationDays').value) || 5;
  const start = new Date(this.value);
  if (!isNaN(start)) {
    start.setDate(start.getDate() + days);
    document.getElementById('endDate').value = start.toISOString().split('T')[0];
  }
});

document.getElementById('durationDays')?.addEventListener('change', function() {
  const startVal = document.getElementById('startDate').value;
  if (!startVal) return;
  const start = new Date(startVal);
  start.setDate(start.getDate() + parseInt(this.value));
  document.getElementById('endDate').value = start.toISOString().split('T')[0];
});

// ── Budget chart reference ───────────────────────────────────────────────────
let budgetChartInstance = null;

// ── Generate Itinerary ───────────────────────────────────────────────────────
document.getElementById('generateBtn')?.addEventListener('click', generateItinerary);

async function generateItinerary() {
  const destination = document.getElementById('destination').value.trim();
  if (!destination) {
    showToast('Please enter a destination.', 'warning');
    return;
  }

  const selectedInterests = [...document.querySelectorAll('#interestTags .interest-tag.selected')]
    .map(t => t.dataset.tag);

  const payload = {
    destination,
    duration_days: parseInt(document.getElementById('durationDays').value) || 5,
    travelers: parseInt(document.getElementById('travelers').value) || 1,
    start_date: document.getElementById('startDate').value,
    end_date: document.getElementById('endDate').value,
    travel_style: document.querySelector('input[name="travelStyle"]:checked')?.value || 'mid-range',
    traveler_type: document.getElementById('travelerType').value,
    budget_inr: parseFloat(document.getElementById('budgetInr').value) || 50000,
    is_international: document.getElementById('isInternational').checked,
    interests: selectedInterests,
  };

  setLoadingState(true);

  try {
    const res = await fetch('/api/itinerary/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.error) { showToast(data.error, 'danger'); return; }

    // Render itinerary
    document.getElementById('itineraryText').innerHTML = formatAIText(data.itinerary);
    document.getElementById('plannerPlaceholder').style.display = 'none';
    document.getElementById('itineraryResult').style.display = 'block';

    // Render budget breakdown
    renderBudgetBreakdown(data.budget_breakdown, payload);

    // Store trip data for saving
    window._currentTrip = { ...payload, itinerary_text: data.itinerary, budget_breakdown: data.budget_breakdown };

    showToast('Itinerary generated successfully!', 'success');
  } catch (err) {
    showToast('Failed to generate itinerary. Check AI service connection.', 'danger');
  } finally {
    setLoadingState(false);
  }
}

// ── Render Budget Breakdown ───────────────────────────────────────────────────
function renderBudgetBreakdown(bb, payload) {
  if (!bb) return;

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

  // Stat mini-cards
  const cardsContainer = document.getElementById('budgetCards');
  cardsContainer.innerHTML = '';
  categories.forEach((cat, i) => {
    const card = document.createElement('div');
    card.className = 'col-6 col-sm-4';
    card.innerHTML = `
      <div class="budget-stat-card">
        <div class="budget-stat-label">${labels[i]}</div>
        <div class="budget-stat-value" style="color:${themeColors[i]}">₹${formatNum(bb[cat])}</div>
      </div>`;
    cardsContainer.appendChild(card);
  });

  // Total display
  const totalCard = document.createElement('div');
  totalCard.className = 'col-12 mt-1';
  totalCard.innerHTML = `
    <div class="total-budget-display">
      Total Estimated Cost: ₹${formatNum(bb.total)} for ${payload.travelers} traveler(s)
    </div>`;
  cardsContainer.appendChild(totalCard);

  // Doughnut chart
  if (budgetChartInstance) budgetChartInstance.destroy();
  const ctx = document.getElementById('budgetChart').getContext('2d');
  budgetChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: categories.map(c => bb[c]),
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#fff',
      }],
    },
    options: {
      responsive: true,
      cutout: '60%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim(),
            font: { size: 12 },
            padding: 14,
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

// ── Get Travel Tips ───────────────────────────────────────────────────────────
document.getElementById('tipsBtn')?.addEventListener('click', async () => {
  const destination = document.getElementById('destination').value.trim();
  if (!destination) { showToast('Enter a destination first.', 'warning'); return; }

  const tipsResult = document.getElementById('tipsResult');
  tipsResult.style.display = 'block';
  document.getElementById('tipsText').innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary"></div></div>';

  try {
    const res = await fetch('/api/travel-tips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination,
        traveler_type: document.getElementById('travelerType').value,
        travel_month: new Date().toLocaleString('default', { month: 'long' }),
      }),
    });
    const data = await res.json();
    document.getElementById('tipsText').innerHTML = formatAIText(data.tips || data.error);
  } catch {
    document.getElementById('tipsText').innerHTML = '<p class="text-danger">Failed to load tips.</p>';
  }
});

// ── Get Packing List ──────────────────────────────────────────────────────────
document.getElementById('packingBtn')?.addEventListener('click', async () => {
  const destination = document.getElementById('destination').value.trim();
  if (!destination) { showToast('Enter a destination first.', 'warning'); return; }

  const packingResult = document.getElementById('packingResult');
  packingResult.style.display = 'block';
  document.getElementById('packingText').innerHTML = '<div class="text-center py-3"><div class="spinner-border text-info"></div></div>';

  try {
    const res = await fetch('/api/packing-list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination,
        duration_days: parseInt(document.getElementById('durationDays').value) || 5,
        activities: [...document.querySelectorAll('#interestTags .interest-tag.selected')].map(t => t.dataset.tag),
        travel_month: new Date().toLocaleString('default', { month: 'long' }),
      }),
    });
    const data = await res.json();
    document.getElementById('packingText').innerHTML = formatAIText(data.checklist || data.error);
  } catch {
    document.getElementById('packingText').innerHTML = '<p class="text-danger">Failed to load packing list.</p>';
  }
});

// ── Family Trip ────────────────────────────────────────────────────────────────
document.getElementById('familyPlanBtn')?.addEventListener('click', async () => {
  const destination = document.getElementById('destination').value.trim();
  if (!destination) { showToast('Enter a destination first.', 'warning'); return; }

  const agesRaw = document.getElementById('childrenAges').value;
  const childrenAges = agesRaw.split(',').map(a => parseInt(a.trim())).filter(a => !isNaN(a));

  setLoadingState(true);
  try {
    const res = await fetch('/api/family-trip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination,
        duration_days: parseInt(document.getElementById('durationDays').value),
        adults: parseInt(document.getElementById('adultsCount').value),
        children_ages: childrenAges,
        budget_inr: parseFloat(document.getElementById('budgetInr').value),
      }),
    });
    const data = await res.json();
    document.getElementById('plannerPlaceholder').style.display = 'none';
    document.getElementById('itineraryResult').style.display = 'block';
    document.getElementById('itineraryText').innerHTML = formatAIText(data.plan || data.error);
    showToast('Family trip plan ready!', 'success');
  } catch {
    showToast('Failed to generate family plan.', 'danger');
  } finally {
    setLoadingState(false);
  }
});

// ── Export PDF ────────────────────────────────────────────────────────────────
document.getElementById('exportPdfBtn')?.addEventListener('click', async () => {
  if (!window._currentTrip) {
    showToast('Please generate an itinerary before exporting PDF.', 'warning');
    return;
  }
  showToast('Generating PDF…', 'info', 3000);
  try {
    const res = await fetch('/api/itinerary/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(window._currentTrip),
    });
    if (!res.ok) {
      let errMsg = 'PDF export failed. Please try again.';
      try { const err = await res.json(); errMsg = err.error || errMsg; } catch {}
      showToast(errMsg, 'danger', 5000);
      return;
    }
    const blob = await res.blob();
    if (!blob || blob.size === 0) {
      showToast('PDF export failed: empty response. Please try again.', 'danger', 5000);
      return;
    }
    // Build filename: Trip_Report_<Destination>_<YYYY-MM-DD>.pdf
    const dest = (window._currentTrip.destination || 'Trip').replace(/\s+/g, '_');
    const today = new Date().toISOString().split('T')[0];
    const filename = `Trip_Report_${dest}_${today}.pdf`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('PDF downloaded successfully!', 'success');
  } catch (err) {
    console.error('PDF export error:', err);
    showToast('PDF export failed. Check your connection and try again.', 'danger', 5000);
  }
});

// ── Save Trip ─────────────────────────────────────────────────────────────────
document.getElementById('saveTripBtn')?.addEventListener('click', async () => {
  if (!window._currentTrip) {
    showToast('Generate an itinerary first.', 'warning');
    return;
  }
  try {
    const res = await fetch('/api/trip/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(window._currentTrip),
    });
    const data = await res.json();
    if (data.status === 'ok') showToast('Trip saved successfully!', 'success');
  } catch {
    showToast('Failed to save trip.', 'danger');
  }
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function setLoadingState(loading) {
  document.getElementById('loadingSkeleton').style.display = loading ? 'block' : 'none';
  if (loading) {
    document.getElementById('itineraryResult').style.display = 'none';
    document.getElementById('plannerPlaceholder').style.display = 'none';
  }
  document.getElementById('generateBtn').disabled = loading;
  document.getElementById('generateBtn').innerHTML = loading
    ? '<span class="spinner-border spinner-border-sm me-2"></span>Generating…'
    : '<i class="bi bi-magic me-2"></i>Generate Itinerary';
}

function formatNum(n) {
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}
