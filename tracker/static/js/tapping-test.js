document.addEventListener('DOMContentLoaded', function () {
  const tapButton = document.getElementById('tap-button');
  const testTime = document.getElementById('test-time');
  const testTaps = document.getElementById('test-taps');

  let startTime = null;
  let tapCount = 0;

  function start() {
    startTime = performance.now();
    tapCount = 0;
    const interval = setInterval(function () {
      const elapsedTime = (performance.now() - startTime) / 1000;
      testTime.textContent = elapsedTime.toFixed(0);
    }, 100);

    setTimeout(function () {
      clearInterval(interval);
      tapButton.disabled = true;
      const durationInput = document.getElementById('id_duration');
      const tapsInput = document.getElementById('id_taps');
      durationInput.value = ((performance.now() - startTime) / 1000).toFixed(0);
      tapsInput.value = tapCount;
      document.querySelector('button[type="submit"]').hidden = false;
      document.querySelector('button[type="submit"]').disabled = false;
    }, 10000);
  }

  tapButton.addEventListener('click', function () {
    if (!startTime) {
      start();
    }
    tapCount++;
    testTaps.textContent = tapCount;
  });

  tapButton.focus();
});
