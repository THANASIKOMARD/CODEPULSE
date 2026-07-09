async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

// --- Hotspot table -----------------------------------------------------

async function loadHotspots() {
  const data = await api("/api/latest");
  document.querySelector("#run-info").textContent =
    `run #${data.run_id} — ${new Date(data.timestamp * 1000).toLocaleString()}`;

  const tbody = document.querySelector("#hotspot-table tbody");
  tbody.innerHTML = "";
  for (const f of data.files) {
    const tr = document.createElement("tr");
    if (f.bus_factor_risk) tr.classList.add("risk");
    tr.innerHTML = `
      <td>${f.roi.toFixed(0)}</td>
      <td>${f.score}</td>
      <td>${f.commits}</td>
      <td>${f.complexity}</td>
      <td>${f.role}</td>
      <td>${f.links}</td>
      <td>${f.num_authors}</td>
      <td class="path">${f.path}</td>
    `;
    tbody.appendChild(tr);
  }
}

// --- Trend chart ---------------------------------------------------------

let trendChart = null;

async function loadTrendChart(path) {
  const rows = await api(`/api/trend/${path.split("/").map(encodeURIComponent).join("/")}`);
  const labels = rows.map((r) => new Date(r.timestamp * 1000).toLocaleDateString());
  const roi = rows.map((r) => r.roi);

  if (trendChart) trendChart.destroy();
  trendChart = new Chart(document.querySelector("#trend-chart"), {
    type: "line",
    data: { labels, datasets: [{ label: "roi", data: roi, borderColor: "#58a6ff", tension: 0.2 }] },
    options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true } } },
  });
}

async function initTrendPicker() {
  const paths = await api("/api/paths");
  const select = document.querySelector("#trend-file");
  select.innerHTML = paths.map((p) => `<option value="${p}">${p}</option>`).join("");
  select.addEventListener("change", () => loadTrendChart(select.value));
  if (paths.length) loadTrendChart(paths[0]);
}

// --- Drift chart -----------------------------------------------------

let driftChart = null;

function driftDelta(d) {
  // roi went up = getting riskier (red); down = improving (green);
  // added counts as pure upside risk, removed as pure downside relief.
  if (d.status === "changed") return d.new.roi - d.old.roi;
  if (d.status === "added") return d.new.roi;
  return -d.old.roi;
}

async function loadDriftChart() {
  const from = document.querySelector("#drift-from").value;
  const to = document.querySelector("#drift-to").value;
  const drifts = await api(`/api/drift?from_run=${from}&to_run=${to}`);

  const top = drifts.slice(0, 10);
  const values = top.map(driftDelta);

  if (driftChart) driftChart.destroy();
  driftChart = new Chart(document.querySelector("#drift-chart"), {
    type: "bar",
    data: {
      labels: top.map((d) => d.path),
      datasets: [{
        label: "Δ roi",
        data: values,
        backgroundColor: values.map((v) => (v >= 0 ? "#f85149" : "#3fb950")),
      }],
    },
    options: { maintainAspectRatio: false, indexAxis: "y" },
  });
}

async function initDriftPickers() {
  const runs = await api("/api/runs");
  const opts = runs
    .map((r) => `<option value="${r.run_id}">#${r.run_id} — ${new Date(r.timestamp * 1000).toLocaleString()}</option>`)
    .join("");
  document.querySelector("#drift-from").innerHTML = opts;
  document.querySelector("#drift-to").innerHTML = opts;

  if (runs.length >= 2) {
    document.querySelector("#drift-from").value = runs[runs.length - 2].run_id;
    document.querySelector("#drift-to").value = runs[runs.length - 1].run_id;
    loadDriftChart();
  }
  document.querySelector("#drift-compare").addEventListener("click", loadDriftChart);
}

// --- Decay panel -----------------------------------------------------

async function loadDecayPanel() {
  const threshold = document.querySelector("#decay-threshold").value || 500;
  const withinDays = document.querySelector("#decay-within-days").value || 30;
  const forecasts = await api(`/api/predict?threshold=${threshold}&within_days=${withinDays}`);

  const tbody = document.querySelector("#decay-table tbody");
  tbody.innerHTML = "";
  if (!forecasts.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="path">No files predicted to cross the threshold in this window.</td></tr>`;
    return;
  }
  for (const f of forecasts) {
    const crossDate = new Date(f.predicted_cross_timestamp * 1000).toLocaleDateString();
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${f.days_until_cross.toFixed(1)}</td>
      <td>${crossDate}</td>
      <td>${f.current_roi.toFixed(0)}</td>
      <td>${f.slope.toFixed(2)}</td>
      <td class="path">${f.path}</td>
    `;
    tbody.appendChild(tr);
  }
}

document.querySelector("#decay-refresh").addEventListener("click", loadDecayPanel);

// --- Boot -----------------------------------------------------------

window.addEventListener("DOMContentLoaded", () => {
  loadHotspots();
  initTrendPicker();
  initDriftPickers();
  loadDecayPanel();
});