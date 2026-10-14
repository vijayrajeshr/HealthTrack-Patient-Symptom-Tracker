(function () {
  'use strict';

  // Elements
  const userInput = document.getElementById('user');
  const form = document.getElementById('form');
  const symptomInput = document.getElementById('symptom');
  const knownDatalist = document.getElementById('known');
  const scaleContainer = document.getElementById('scale');
  const scaleHint = document.getElementById('scale-hint');
  const dateInput = document.getElementById('date');
  const formErr = document.getElementById('form-err');
  const rangeErr = document.getElementById('range-err');
  const startInput = document.getElementById('start');
  const endInput = document.getElementById('end');
  const clearBtn = document.getElementById('clear');
  const insightsContainer = document.getElementById('insights');
  const entriesList = document.getElementById('entries');
  const countSpan = document.getElementById('count');
  const toastEl = document.getElementById('toast');

  let selectedSeverity = null;
  let toastTimer = null;

  const severityHints = {
    1: '1: Barely noticeable',
    2: '2: Very mild',
    3: '3: Mild',
    4: '4: Noticeable',
    5: '5: Moderate',
    6: '6: Uncomfortable',
    7: '7: Strong / Painful',
    8: '8: Severe',
    9: '9: Very severe',
    10: '10: Worst possible',
  };

  const severityColors = {
    1: '#10b981',
    2: '#22c55e',
    3: '#84cc16',
    4: '#a3e635',
    5: '#eab308',
    6: '#f59e0b',
    7: '#f97316',
    8: '#ea580c',
    9: '#ef4444',
    10: '#b91c1c',
  };

  // Format today as YYYY-MM-DD
  function getTodayString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // Escape HTML entities to prevent XSS
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Toast notification
  function showToast(message, type = 'success') {
    if (toastTimer) clearTimeout(toastTimer);
    toastEl.textContent = message;
    toastEl.className = `show ${type}`;
    toastTimer = setTimeout(() => {
      toastEl.className = '';
    }, 3200);
  }

  // Clear field errors
  function clearErrors() {
    document.querySelectorAll('.err').forEach((el) => (el.textContent = ''));
    document.querySelectorAll('.has-err').forEach((el) => el.classList.remove('has-err'));
  }

  function setFieldError(field, message) {
    const errEl = document.querySelector(`.err[data-for="${field}"]`);
    if (errEl) errEl.textContent = message;
    const inputEl = document.getElementById(field);
    if (inputEl) inputEl.classList.add('has-err');
  }

  // Severity Scale Setup
  function initSeverityScale() {
    scaleContainer.innerHTML = '';
    for (let i = 1; i <= 10; i++) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'scale-btn';
      btn.setAttribute('role', 'radio');
      btn.setAttribute('aria-checked', 'false');
      btn.setAttribute('aria-label', `Severity ${i}`);
      btn.dataset.sev = i;
      btn.textContent = i;

      btn.addEventListener('mouseenter', () => {
        scaleHint.textContent = severityHints[i];
      });

      btn.addEventListener('mouseleave', () => {
        if (selectedSeverity) {
          scaleHint.textContent = severityHints[selectedSeverity];
        } else {
          scaleHint.textContent = 'Pick 1 (barely there) to 10 (worst).';
        }
      });

      btn.addEventListener('click', () => {
        selectSeverity(i);
      });

      scaleContainer.appendChild(btn);
    }
  }

  function selectSeverity(val) {
    selectedSeverity = val;
    scaleContainer.querySelectorAll('.scale-btn').forEach((btn) => {
      const isMatch = parseInt(btn.dataset.sev, 10) === val;
      btn.classList.toggle('active', isMatch);
      btn.setAttribute('aria-checked', isMatch ? 'true' : 'false');
    });
    scaleHint.textContent = severityHints[val];
    const errEl = document.querySelector('.err[data-for="severity"]');
    if (errEl) errEl.textContent = '';
  }

  function resetSeverity() {
    selectedSeverity = null;
    scaleContainer.querySelectorAll('.scale-btn').forEach((btn) => {
      btn.classList.remove('active');
      btn.setAttribute('aria-checked', 'false');
    });
    scaleHint.textContent = 'Pick 1 (barely there) to 10 (worst).';
  }

  // Load known symptoms into autocomplete datalist
  function updateAutocomplete(symptoms) {
    const unique = [...new Set(symptoms.map((s) => s.symptom))].sort();
    knownDatalist.innerHTML = '';
    unique.forEach((name) => {
      const opt = document.createElement('option');
      opt.value = name;
      knownDatalist.appendChild(opt);
    });
  }

  // Render entries list
  function renderEntries(symptoms) {
    entriesList.innerHTML = '';
    countSpan.textContent = `(${symptoms.length})`;

    if (symptoms.length === 0) {
      const emptyLi = document.createElement('li');
      emptyLi.className = 'empty-state';
      emptyLi.textContent = 'No entries found. Log your first symptom above!';
      entriesList.appendChild(emptyLi);
      return;
    }

    symptoms.forEach((entry) => {
      const li = document.createElement('li');
      li.className = 'entry-item';

      const infoDiv = document.createElement('div');
      infoDiv.className = 'entry-info';

      const dateSpan = document.createElement('span');
      dateSpan.className = 'entry-date';
      dateSpan.textContent = entry.date;

      const symSpan = document.createElement('span');
      symSpan.className = 'entry-sym';
      symSpan.textContent = entry.symptom;

      infoDiv.appendChild(dateSpan);
      infoDiv.appendChild(symSpan);

      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'entry-actions';

      const sevChip = document.createElement('span');
      sevChip.className = 'sev-chip';
      sevChip.style.backgroundColor = severityColors[entry.severity] || '#6366f1';
      sevChip.textContent = entry.severity;
      sevChip.title = `Severity ${entry.severity}/10`;

      const delBtn = document.createElement('button');
      delBtn.className = 'btn-del';
      delBtn.type = 'button';
      delBtn.innerHTML = '&times;';
      delBtn.title = 'Delete entry';
      delBtn.setAttribute('aria-label', `Delete ${entry.symptom} on ${entry.date}`);

      delBtn.addEventListener('click', async () => {
        if (!confirm(`Delete entry for "${entry.symptom}" on ${entry.date}?`)) return;
        try {
          const res = await fetch(`/api/symptoms/${entry.id}?user_id=${encodeURIComponent(getCurrentUser())}`, {
            method: 'DELETE',
          });
          if (res.status === 204) {
            showToast('Entry deleted.');
            loadData();
          } else {
            const data = await res.json();
            showToast(data.error || 'Could not delete entry.', 'error');
          }
        } catch {
          showToast('Could not reach server to delete.', 'error');
        }
      });

      actionsDiv.appendChild(sevChip);
      actionsDiv.appendChild(delBtn);

      li.appendChild(infoDiv);
      li.appendChild(actionsDiv);
      entriesList.appendChild(li);
    });
  }

  // Render insights dashboard
  function renderInsights(insights) {
    insightsContainer.innerHTML = '';

    if (!insights || insights.total_entries === 0) {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'empty-state';
      emptyDiv.textContent = insights.message || 'Log symptoms to reveal patterns and insights.';
      insightsContainer.appendChild(emptyDiv);
      return;
    }

    // KPI Grid
    const kpiGrid = document.createElement('div');
    kpiGrid.className = 'kpi-grid';

    // Total
    const kpiTotal = document.createElement('div');
    kpiTotal.className = 'kpi-card';
    kpiTotal.innerHTML = `<span class="kpi-label">Total Entries</span><span class="kpi-val">${insights.total_entries}</span>`;
    kpiGrid.appendChild(kpiTotal);

    // Average Severity
    const kpiAvg = document.createElement('div');
    kpiAvg.className = 'kpi-card';
    const roundedAvg = Math.round(insights.average_severity);
    const avgColor = severityColors[roundedAvg] || '#6366f1';
    kpiAvg.innerHTML = `<span class="kpi-label">Avg Severity</span><span class="kpi-val" style="color:${avgColor}">${insights.average_severity}<small style="font-size:0.9rem;color:var(--text-dim)">/10</small></span>`;
    kpiGrid.appendChild(kpiAvg);

    // Highest Entry
    const kpiPeak = document.createElement('div');
    kpiPeak.className = 'kpi-card';
    if (insights.highest_entry) {
      const peakColor = severityColors[insights.highest_entry.severity] || '#6366f1';
      const labelSpan = document.createElement('span');
      labelSpan.className = 'kpi-label';
      labelSpan.textContent = 'Peak Entry';

      const valSpan = document.createElement('span');
      valSpan.className = 'kpi-val';
      valSpan.style.color = peakColor;
      valSpan.textContent = `${insights.highest_entry.severity}`;

      const symSpan = document.createElement('span');
      symSpan.style.fontSize = '0.8rem';
      symSpan.style.fontWeight = '500';
      symSpan.style.textTransform = 'capitalize';
      symSpan.style.color = 'var(--text-muted)';
      symSpan.style.marginLeft = '0.35rem';
      symSpan.textContent = `(${insights.highest_entry.symptom})`;

      valSpan.appendChild(symSpan);
      kpiPeak.appendChild(labelSpan);
      kpiPeak.appendChild(valSpan);
    } else {
      kpiPeak.innerHTML = `<span class="kpi-label">Peak Entry</span><span class="kpi-val">-</span>`;
    }
    kpiGrid.appendChild(kpiPeak);

    // Trend
    const kpiTrend = document.createElement('div');
    kpiTrend.className = 'kpi-card';
    if (insights.trend) {
      kpiTrend.innerHTML = `
        <span class="kpi-label">2-Week Trend</span>
        <span class="kpi-val"><span class="badge-trend ${insights.trend}">${insights.trend}</span></span>
      `;
    } else {
      kpiTrend.innerHTML = `
        <span class="kpi-label">2-Week Trend</span>
        <span class="kpi-val"><span class="badge-trend steady">Need &ge; 2 wks</span></span>
      `;
    }
    kpiGrid.appendChild(kpiTrend);

    insightsContainer.appendChild(kpiGrid);

    // Weekly Averages Chart
    if (insights.weekly_averages && insights.weekly_averages.length > 0) {
      const chartHead = document.createElement('h3');
      chartHead.className = 'section-subhead';
      chartHead.textContent = 'Weekly Average Severity';
      insightsContainer.appendChild(chartHead);

      const chartDiv = document.createElement('div');
      chartDiv.className = 'weekly-chart';

      insights.weekly_averages.forEach((w) => {
        const row = document.createElement('div');
        row.className = 'chart-row';

        const dateSpan = document.createElement('span');
        dateSpan.className = 'chart-date';
        dateSpan.textContent = `w/c ${w.week_start.slice(5)}`;

        const barBg = document.createElement('div');
        barBg.className = 'chart-bar-bg';

        const barFill = document.createElement('div');
        barFill.className = 'chart-bar-fill';
        const percent = Math.min(100, Math.max(8, (w.average_severity / 10) * 100));
        barFill.style.width = `${percent}%`;
        const col = severityColors[Math.round(w.average_severity)] || '#6366f1';
        barFill.style.backgroundColor = col;

        barBg.appendChild(barFill);

        const scoreSpan = document.createElement('span');
        scoreSpan.className = 'chart-score';
        scoreSpan.textContent = `${w.average_severity}`;

        row.appendChild(dateSpan);
        row.appendChild(barBg);
        row.appendChild(scoreSpan);
        chartDiv.appendChild(row);
      });

      insightsContainer.appendChild(chartDiv);
    }

    // Top Symptoms
    if (insights.most_common && insights.most_common.length > 0) {
      const commonHead = document.createElement('h3');
      commonHead.className = 'section-subhead';
      commonHead.textContent = 'Most Common Symptoms';
      insightsContainer.appendChild(commonHead);

      const commonList = document.createElement('div');
      commonList.className = 'common-list';

      insights.most_common.forEach((item) => {
        const div = document.createElement('div');
        div.className = 'common-item';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'common-name';
        nameSpan.textContent = item.symptom;

        const metaSpan = document.createElement('div');
        metaSpan.className = 'common-meta';
        metaSpan.innerHTML = `
          <span>${item.count} ${item.count === 1 ? 'entry' : 'entries'}</span>
          <span class="sev-chip" style="background:${severityColors[Math.round(item.average_severity)] || '#6366f1'}">avg ${item.average_severity}</span>
        `;

        div.appendChild(nameSpan);
        div.appendChild(metaSpan);
        commonList.appendChild(div);
      });

      insightsContainer.appendChild(commonList);
    }
  }

  // User ID helper
  function getCurrentUser() {
    return (userInput.value || '').trim() || 'demo';
  }

  // Fetch and display entries & insights
  async function loadData() {
    const user = getCurrentUser();
    if (!user) return;

    rangeErr.textContent = '';
    const params = new URLSearchParams({ user_id: user });
    if (startInput.value) params.set('start', startInput.value);
    if (endInput.value) params.set('end', endInput.value);

    try {
      const [symptomsRes, insightsRes] = await Promise.all([
        fetch(`/api/symptoms?${params.toString()}`),
        fetch(`/api/insights?${params.toString()}`),
      ]);

      if (symptomsRes.ok) {
        const symptomsData = await symptomsRes.json();
        renderEntries(symptomsData.symptoms || []);
        updateAutocomplete(symptomsData.symptoms || []);
      } else {
        const errData = await symptomsRes.json();
        if (errData.details) {
          if (errData.details.range) rangeErr.textContent = errData.details.range;
          if (errData.details.start) rangeErr.textContent = errData.details.start;
          if (errData.details.end) rangeErr.textContent = errData.details.end;
        }
      }

      if (insightsRes.ok) {
        const insightsData = await insightsRes.json();
        renderInsights(insightsData);
      }
    } catch {
      showToast('Cannot connect to server.', 'error');
    }
  }

  // Handle Form Submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const payload = {
      user_id: getCurrentUser(),
      symptom: symptomInput.value,
      severity: selectedSeverity,
      date: dateInput.value,
    };

    try {
      const res = await fetch('/api/symptoms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.status === 201) {
        showToast('Symptom logged successfully!');
        symptomInput.value = '';
        resetSeverity();
        dateInput.value = getTodayString();
        loadData();
      } else {
        if (data.details) {
          Object.entries(data.details).forEach(([field, msg]) => {
            setFieldError(field, msg);
          });
        }
        if (data.error && !data.details) {
          formErr.textContent = data.error;
        }
        showToast(data.error || 'Please correct errors.', 'error');
      }
    } catch {
      showToast('Cannot reach the server.', 'error');
    }
  });

  // User input change
  userInput.addEventListener('change', () => {
    localStorage.setItem('healthtrack_user', getCurrentUser());
    loadData();
  });

  // Date filters
  startInput.addEventListener('change', loadData);
  endInput.addEventListener('change', loadData);

  clearBtn.addEventListener('click', () => {
    startInput.value = '';
    endInput.value = '';
    rangeErr.textContent = '';
    loadData();
  });

  // Initialization
  function init() {
    const today = getTodayString();
    dateInput.value = today;
    dateInput.max = today;

    // Restore saved user
    const savedUser = localStorage.getItem('healthtrack_user');
    if (savedUser) {
      userInput.value = savedUser;
    }

    initSeverityScale();
    loadData();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
