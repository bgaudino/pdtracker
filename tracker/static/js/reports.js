document.addEventListener('DOMContentLoaded', function () {
  const data = JSON.parse(document.getElementById('reports-data').textContent);
  const checkinChart = document.getElementById('checkin-chart');

  new Chart(checkinChart, {
    type: 'line',
    data: {
      labels: Object.keys(data.checkin),
      datasets: [
        {
          label: 'Pain',
          data: Object.values(data.checkin).map((item) => item.pain),
          borderWidth: 1,
        },
        {
          label: 'Bradykinesia',
          data: Object.values(data.checkin).map((item) => item.bradykinesia),
          borderWidth: 1,
        },
        {
          label: 'Rigidity',
          data: Object.values(data.checkin).map((item) => item.rigidity),
          borderWidth: 1,
        },
        {
          label: 'Fatigue',
          data: Object.values(data.checkin).map((item) => item.fatigue),
          borderWidth: 1,
        },
        {
          label: 'Hand Dysfunction',
          data: Object.values(data.checkin).map(
            (item) => item.hand_dysfunction,
          ),
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Hours Since Last Medication',
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Severity',
          },
        },
      },
    },
  });

  const tappingChart = document.getElementById('tapping-chart');

  new Chart(tappingChart, {
    type: 'line',
    data: {
      labels: Object.keys(data.tappingtest),
      datasets: [
        {
          label: 'Taps Per Second',
          data: Object.values(data.tappingtest).map(
            (item) => item.taps_per_second,
          ),
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Hours Since Last Medication',
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Taps Per Second',
          },
        },
      },
    },
  });

  const typingChart = document.getElementById('typing-chart');

  new Chart(typingChart, {
    type: 'line',
    data: {
      labels: Object.keys(data.typingtest),
      datasets: [
        {
          label: 'WPM',
          data: Object.values(data.typingtest).map((item) => item.wpm),
          borderWidth: 1,
        },
        {
          label: 'Accuracy',
          data: Object.values(data.typingtest).map((item) => item.accuracy),
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Hours Since Last Medication',
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Performance',
          },
        },
      },
    },
  });

  const activityChart = document.getElementById('activity-chart');

  new Chart(activityChart, {
    type: 'line',
    data: {
      labels: Object.keys(data.activitylog),
      datasets: [
        {
          label: 'Dystonia Onset',
          data: Object.values(data.activitylog).map(
            (item) => item.dystonia_onset,
          ),
          borderWidth: 1,
        },
        {
          label: 'Dystonia Severity',
          data: Object.values(data.activitylog).map(
            (item) => item.dystonia_severity,
          ),
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Hours Since Last Medication',
          },
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Severity',
          },
        },
      },
    },
  });
});
