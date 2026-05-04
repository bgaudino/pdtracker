document.addEventListener('DOMContentLoaded', function () {
  const filterForm = document.getElementById('filter-form');
  if (filterForm) {
    filterForm.addEventListener('change', function () {
      this.submit();
    });
  }
});
