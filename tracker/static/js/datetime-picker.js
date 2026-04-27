document.addEventListener('DOMContentLoaded', function () {
  flatpickr('#id_timestamp', {
    enableTime: true,
    altInput: true,
    altFormat: 'F j, Y h:i K',
    dateFormat: 'Y-m-d\\TH:i',
    minuteIncrement: 1,
  });
});
