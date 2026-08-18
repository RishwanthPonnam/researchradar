document.addEventListener('DOMContentLoaded', () => {

  // Smooth focus ring management — mouse users shouldn't see focus rings
  document.body.addEventListener('mousedown', () => {
    document.body.classList.add('using-mouse');
  });
  document.body.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') document.body.classList.remove('using-mouse');
  });

  // Auto-focus the home search input (only on the home page)
  const homeSearch = document.getElementById('home-search');
  if (homeSearch) {
    // Small delay so the page-enter animation finishes first
    setTimeout(() => homeSearch.focus(), 320);
  }

  // Loading state for search form submission
  document.querySelectorAll('form[role="search"]').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.textContent = 'Searching...';
        btn.disabled = true;
      }
    });
  });

});
