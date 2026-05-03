document.addEventListener('DOMContentLoaded', function () {
  const toasts = JSON.parse(document.getElementById('toasts-data').textContent);
  toasts.forEach((toast) => {
    Toastify({
      text: toast.text,
      duration: 3000,
      close: true,
      stopOnFocus: true,
    }).showToast();
  });
});
