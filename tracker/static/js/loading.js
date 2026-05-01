document.addEventListener('DOMContentLoaded', function () {
  toggleLoading(false);
  const links = document.querySelectorAll('a');
  const forms = document.querySelectorAll('form');

  function showLoading() {
    setTimeout(() => toggleLoading(true), 0);
  }

  links.forEach((link) => {
    link.addEventListener('click', showLoading);
  });

  forms.forEach((form) => {
    form.addEventListener('submit', showLoading);
  });
});

window.addEventListener('pageshow', function () {
  toggleLoading(false);
});

function toggleLoading(show) {
  const loading = document.getElementById('loading-indicator');
  if (loading) {
    loading.setAttribute('aria-busy', show ? 'true' : 'false');
  }
  const forms = document.querySelectorAll('form');
  forms.forEach((form) => {
    for (const button of form.querySelectorAll(
      'button[type="submit"], input[type="submit"]',
    )) {
      button.disabled = show;
    }
    for (const button of document.querySelectorAll(`[form="${form.id}"]`)) {
      button.disabled = show;
    }
  });
}
