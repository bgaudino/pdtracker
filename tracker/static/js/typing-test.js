document.addEventListener('DOMContentLoaded', function () {
  const typingTestForm = document.getElementById('typing-test-form');
  const promptData = JSON.parse(
    document.getElementById('prompt-data').textContent,
  );
  const prompt = promptData.join(' ');
  const promptDisplay = document.getElementById('prompt-display');
  for (const [index, item] of prompt.split('').entries()) {
    const span = document.createElement('span');
    span.textContent = item;
    span.classList.add('prompt-char');
    span.dataset.index = index;
    if (index === 0) {
      span.classList.add('current');
    }
    promptDisplay.appendChild(span);
  }

  let started = false;
  let timeRemaining = 30;
  const userInput = document.getElementById('typing-input');
  const timer = document.getElementById('timer');
  let timerInterval;

  function start() {
    started = true;
    timerInterval = setInterval(function () {
      timeRemaining--;
      timer.textContent = timeRemaining;
      if (timeRemaining <= 0) {
        end();
      }
    }, 1000);
  }

  function end() {
    clearInterval(timerInterval);
    userInput.disabled = true;
    updateResults();
    document.getElementById('save-results-button').hidden = false;
  }

  function updateResults() {
    const inputValue = userInput.value;
    const promptChars = document.querySelectorAll('.prompt-char');
    let correctChars = 0;
    let errors = 0;
    for (let i = 0; i < inputValue.length; i++) {
      const char = promptChars[i];
      if (!char) break;
      if (inputValue[i] === char.textContent) {
        correctChars++;
        char.classList.add('correct');
      } else {
        errors++;
        char.classList.add('incorrect');
      }
    }
    const accuracy =
      correctChars + errors > 0
        ? (correctChars / (correctChars + errors)) * 100
        : 0;
    document.getElementById('accuracy').textContent = `${accuracy.toFixed(2)}%`;
    const wpm = correctChars / 5 / ((30 - timeRemaining) / 60);
    document.getElementById('wpm').textContent = wpm.toFixed(2);
    document.getElementById('id_typed').value = inputValue;
    document.getElementById('id_time_seconds').value = 30 - timeRemaining;
  }

  userInput.addEventListener('input', function () {
    if (!started) {
      start();
    }

    const inputValue = userInput.value;
    const promptChars = document.querySelectorAll('.prompt-char');
    for (const char of promptChars) {
      char.classList.remove('current', 'correct', 'incorrect');
    }

    updateResults();

    const currentChar = promptChars[inputValue.length];
    if (currentChar) {
      currentChar.classList.add('current');
    } else {
      end();
    }
  });
});
