document.addEventListener('DOMContentLoaded', function () {
  const links = document.querySelectorAll('a');
  const forms = document.querySelectorAll('form');

  function showLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
      setTimeout(() => {
        loading.setAttribute('aria-busy', 'true');
      }, 1000);
    }
  }

  links.forEach((link) => {
    link.addEventListener('click', showLoading);
  });

  forms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      for (const button of form.querySelectorAll(
        'button[type="submit"], input[type="submit"]',
      )) {
        button.disabled = true;
      }
      for (const button of document.querySelectorAll(`[form="${form.id}"]`)) {
        button.disabled = true;
      }
      showLoading();
    });
  });
});
