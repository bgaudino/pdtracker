document.addEventListener('DOMContentLoaded', function () {
  const select = document.getElementById('id_data_type');
  if (select) {
    select.addEventListener('change', function () {
      const selectedType = this.value;
      const url = new URL(window.location.href);
      const pathParts = url.pathname.split('/').filter(Boolean);
      pathParts[pathParts.length - 1] = selectedType;
      url.pathname = `/${pathParts.join('/')}/`;
      window.location.href = url.toString();
    });
  }

  const ctx = document.getElementById('health-metric-chart').getContext('2d');
  const data = JSON.parse(
    document.getElementById('health-metric-data').textContent,
  );
  const title = JSON.parse(
    document.getElementById('health-metric-title').textContent,
  );

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map((entry) => entry.date),
      datasets: [
        {
          label: title,
          data: data.map((entry) => entry.value),
        },
      ],
    },
  });
});
