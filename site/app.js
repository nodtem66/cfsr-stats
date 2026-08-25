// ─── Base URL for raw JSON stats ────────────────────────────────────────────
const BASE = 'https://raw.githubusercontent.com/nodtem66/cfsr-stats/refs/heads/main/stats/';

// ─── Color palette for charts ────────────────────────────────────────────────
const COLORS = [
  '#f0883e', '#58a6ff', '#3fb950', '#d2a8ff', '#f85149',
  '#e3b341', '#79c0ff', '#56d364', '#bc8cff', '#ffa657',
  '#7ee787', '#a5d6ff', '#ff7b72', '#c9d1d9', '#f78c6c'
];

const COLORS_ALPHA = COLORS.map(c => c + '80');

let chartInstances = {};

// ─── Helpers ─────────────────────────────────────────────────────────────────
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function show(id) { $(id).classList.remove('hidden'); }
function hide(id) { $(id).classList.add('hidden'); }

function fmt(n) {
  if (typeof n !== 'number') return n;
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function fmtPct(n) {
  if (typeof n !== 'number') return n;
  return (n * 100).toFixed(2) + 'PRs/day';
}

// ─── Fetch all stats ─────────────────────────────────────────────────────────
async function fetchAll() {
  const files = [
    'number_pr_by_lang.json',
    'rate.json',
    'time_to_merge_days.json',
    'top_reviewer_6month.json',
    'top_reviewer_all_time.json'
  ];

  const results = await Promise.all(
    files.map(f =>
      fetch(BASE + f).then(r => {
        if (!r.ok) throw new Error(`Failed to load ${f}: ${r.status}`);
        return r.json();
      })
    )
  );

  return {
    lang: results[0],
    rate: results[1],
    merge: results[2],
    reviewer6: results[3],
    reviewerAll: results[4]
  };
}

// ─── Chart: PRs by Language ──────────────────────────────────────────────────
function renderLangChart(data) {
  const langs = Object.keys(data.lang).sort((a, b) => data.lang[b].total - data.lang[a].total);
  const totals = langs.map(l => data.lang[l].total);
  const closed = langs.map(l => data.lang[l].closed);

  // Destroy previous chart
  if (chartInstances.lang) chartInstances.lang.destroy();

  const ctx = document.getElementById('langChart').getContext('2d');
  chartInstances.lang = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: langs,
      datasets: [
        { label: 'Total PRs', data: totals, backgroundColor: COLORS.slice(0, langs.length), borderRadius: 4 },
        { label: 'Closed PRs', data: closed, backgroundColor: COLORS_ALPHA.slice(0, langs.length), borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#c9d1d9' } } },
      scales: {
        x: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
        y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' }, beginAtZero: true }
      }
    }
  });

  // Table
  const tbody = document.querySelector('#lang-table tbody');
  tbody.innerHTML = '';
  for (const l of langs) {
    const d = data.lang[l];
    const rate = d.total > 0 ? (d.closed / d.total * 100).toFixed(2) + '%' : '—';
    tbody.innerHTML += `<tr><td>${l}</td><td>${fmt(d.total)}</td><td>${fmt(d.closed)}</td><td>${rate}</td></tr>`;
  }

  show('#lang-section');
}

// ─── Chart: Rate by Year ─────────────────────────────────────────────────────
function renderRateChart(data) {
  const years = Object.keys(data.rate).sort();
  const submissions = years.map(y => data.rate[y].submission);
  const accepted = years.map(y => data.rate[y].acceptance);
  const subRate = years.map(y => data.rate[y].submission_rate);
  const accRate = years.map(y => data.rate[y].acceptance_rate);

  if (chartInstances.rate) chartInstances.rate.destroy();

  const ctx = document.getElementById('rateChart').getContext('2d');
  chartInstances.rate = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: years,
      datasets: [
        { label: 'Submissions', data: submissions, backgroundColor: '#58a6ff', borderRadius: 4 },
        { label: 'Accepted', data: accepted, backgroundColor: '#3fb950', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#c9d1d9' } },
        tooltip: {
          callbacks: {
            afterBody: function (tooltipItems) {
              const idx = tooltipItems[0].dataIndex;
              return `Submission Rate: ${subRate[idx].toFixed(2)}\nAcceptance Rate: ${accRate[idx].toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        x: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
        y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' }, beginAtZero: true }
      }
    }
  });

  const tbody = document.querySelector('#rate-table tbody');
  tbody.innerHTML = '';
  for (const y of years) {
    const d = data.rate[y];
    tbody.innerHTML += `
      <tr>
        <td>${y}</td>
        <td>${fmt(d.submission)}</td>
        <td>${fmt(d.acceptance)}</td>
        <td>${d.submission_rate.toFixed(2)}</td>
        <td>${d.acceptance_rate.toFixed(2)}</td>
      </tr>`;
  }

  show('#rate-section');
}

// ─── Chart: Time to Merge ────────────────────────────────────────────────────
function renderMergeChart(data) {
  const sortedLangs = Object.keys(data.lang).sort((a, b) => data.lang[b].total - data.lang[a].total);
  const langs = sortedLangs.filter(l => data.merge[l]?.median !== undefined);
  const labels = langs;
  const medians = langs.map(l => +data.merge[l].median.toFixed(2));
  const p95 = langs.map(l => +data.merge[l].p95.toFixed(2));

  if (chartInstances.merge) chartInstances.merge.destroy();

  const ctx = document.getElementById('mergeChart').getContext('2d');
  chartInstances.merge = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Median (days)', data: medians, backgroundColor: '#d2a8ff', borderRadius: 4 },
        { label: 'P95 (days)', data: p95, backgroundColor: '#f85149', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#c9d1d9' } } },
      scales: {
        x: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
        y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' }, beginAtZero: true }
      }
    }
  });

  const tbody = document.querySelector('#merge-table tbody');
  tbody.innerHTML = '';
  for (const l of langs) {
    const d = data.merge[l];
    tbody.innerHTML += `
      <tr>
        <td>${l}</td>
        <td>${d.min.toFixed(2)}</td>
        <td>${d.median.toFixed(2)}</td>
        <td>${d.p95.toFixed(2)}</td>
      </tr>`;
  }

  show('#merge-section');
}

// ─── Tables: Top Reviewers (no chart, just tables) ───────────────────────────
function renderReviewers(data) {
  function fillTable(id, obj) {
    const tbody = document.querySelector(`#${id} tbody`);
    tbody.innerHTML = '';
    const entries = Object.entries(obj)
      .map(([name, langs]) => [name, langs.total ?? Object.values(langs).reduce((a, b) => a + b, 0)])
      .sort((a, b) => b[1] - a[1]);
    for (const [name, total] of entries) {
      tbody.innerHTML += `<tr><td>${name}</td><td>${fmt(total)}</td></tr>`;
    }
  }

  fillTable('reviewer-6mo-table', data.reviewer6);
  fillTable('reviewer-all-table', data.reviewerAll);
  show('#reviewer-section');
}

// ─── Init ─────────────────────────────────────────────────────────────────────
(async function init() {
  try {
    const data = await fetchAll();
    hide('#loading');
    renderLangChart(data);
    renderRateChart(data);
    renderMergeChart(data);
    renderReviewers(data);
  } catch (err) {
    hide('#loading');
    const el = $('#error');
    el.textContent = '❌ ' + err.message;
    el.classList.remove('hidden');
  }
})();