let chart = null;

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} ${res.status}`);
  return res.json();
}

// load dataset and render (multiple employees)
function renderBarMulti(labels, series) {
  const ctx = document.getElementById('barChart').getContext('2d');
  if (chart) chart.destroy();

  const datasets = series.map((s, i) => ({
    label: s.ename,
    data: s.counts.map(v => parseInt(v, 10) || 0),
    borderWidth: 1,
    backgroundColor: `hsl(${i * 80}, 70%, 60%)`
  }));

  chart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'flight count' },
          ticks: {
            stepSize: 1,
            callback: v => Number.isInteger(v) ? v : ''
          }
        },
        x: { title: { display: true, text: 'Aircraft' } }
      }
    }
  });
}

function renderBarSingle(data) {
  const labels = data.map(r => r.label);
  const values = data.map(r => parseInt(r.flights, 10) || 0);

  const ctx = document.getElementById('barChart').getContext('2d');
  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Flights per aircraft',
        data: values,
        borderWidth: 1,
        backgroundColor: 'rgba(100,149,237,0.5)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'flight count' },
          ticks: {
            stepSize: 1,
            callback: v => Number.isInteger(v) ? v : ''
          }
        },
        x: { title: { display: true, text: 'Aircraft' } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

// table
async function loadEmployeeTable() {
  const { data } = await api('/api/employee-salary-cert');
  const tbody = document.getElementById('empBody');
  tbody.innerHTML = data.map(r => `
    <tr>
      <td><input type="checkbox" class="empCheck" value="${r.eid}" data-name="${r.ename}"></td>
      <td>${r.ename}</td>
      <td class="right">${Number(r.salary).toLocaleString()}</td>
      <td class="right">${r.cert_count}</td>
    </tr>
  `).join('');

  document.querySelectorAll('.empCheck').forEach(cb => {
    cb.addEventListener('change', async () => {
      const selected = Array.from(document.querySelectorAll('.empCheck:checked'));
      if (selected.length > 3) {
        cb.checked = false;
        alert('You can select up to 3 employees for comparison.');
        return;
      }
      await updateChartBySelection();
    });
  });
}

// chart
async function updateChartBySelection() {
  const selected = Array.from(document.querySelectorAll('.empCheck:checked'));
  if (selected.length === 0) {
    const res = await api('/api/flights-per-aircraft');
    return renderBarSingle(res.data || []);
  }

  const ids = selected.map(cb => cb.value).join(',');
  const res = await api(`/api/flights-per-aircraft?eids=${ids}`);

  if (res.series && res.labels) {
    renderBarMulti(res.labels, res.series);
  } else if (res.data) {
    renderBarSingle(res.data);
  }
}

// ---- 初始化 ----
(async () => {
  await loadEmployeeTable();
  await updateChartBySelection(); 
})();
