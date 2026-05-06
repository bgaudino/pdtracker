document.addEventListener('DOMContentLoaded', function () {
  const data = JSON.parse(document.getElementById('reports-data').textContent);
  const checkinChart = document.getElementById('checkin-chart');

  new Chart(checkinChart, {
    type: 'bar',
    data: {
      labels: Object.keys(data.checkin),
      datasets: [
        {
          label: 'Overall Severity',
          data: Object.values(data.checkin).map(
            (item) => item.overall_severity,
          ),
          type: 'line',
        },
        {
          label: 'Rigidity',
          data: Object.values(data.checkin).map((item) => item.rigidity),
          type: 'bar',
        },
        {
          label: 'Bradykinesia',
          data: Object.values(data.checkin).map((item) => item.bradykinesia),
          type: 'bar',
        },
        {
          label: 'Hand Dysfunction',
          data: Object.values(data.checkin).map(
            (item) => item.hand_dysfunction,
          ),
          type: 'bar',
        },
        {
          label: 'Pain',
          data: Object.values(data.checkin).map((item) => item.pain),
          type: 'bar',
        },
        {
          label: 'Fatigue',
          data: Object.values(data.checkin).map((item) => item.fatigue),
          type: 'bar',
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

  const timeOfDayChart = document.getElementById('time-of-day-chart');

  new Chart(timeOfDayChart, {
    type: 'bar',
    data: {
      labels: Object.keys(data.time_of_day),
      datasets: [
        {
          label: 'Overall Severity',
          data: Object.values(data.checkin).map(
            (item) => item.overall_severity,
          ),
          type: 'line',
        },
        {
          label: 'Rigidity',
          data: Object.values(data.checkin).map((item) => item.rigidity),
          type: 'bar',
        },
        {
          label: 'Bradykinesia',
          data: Object.values(data.checkin).map((item) => item.bradykinesia),
          type: 'bar',
        },
        {
          label: 'Hand Dysfunction',
          data: Object.values(data.checkin).map(
            (item) => item.hand_dysfunction,
          ),
          type: 'bar',
        },
        {
          label: 'Pain',
          data: Object.values(data.checkin).map((item) => item.pain),
          type: 'bar',
        },
        {
          label: 'Fatigue',
          data: Object.values(data.checkin).map((item) => item.fatigue),
          type: 'bar',
        },
      ],
    },
    options: {
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Time of Day',
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
    type: 'bar',
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
});
