(function () {
  'use strict';
  var root = document.documentElement;
  var theme = document.getElementById('theme-setting');
  var size = document.getElementById('size-setting');
  function preference(key, fallback) {
    try { return localStorage.getItem('signal-' + key) || fallback; }
    catch (_) { return fallback; }
  }
  function apply(control, key, allowed, fallback) {
    var value = preference(key, fallback);
    if (allowed.indexOf(value) === -1) value = fallback;
    control.value = value;
    root.setAttribute('data-' + key, value);
    control.addEventListener('change', function () {
      root.setAttribute('data-' + key, control.value);
      try { localStorage.setItem('signal-' + key, control.value); } catch (_) { /* Optional persistence. */ }
    });
  }
  apply(theme, 'theme', ['system', 'light', 'dark'], 'system');
  apply(size, 'size', ['standard', 'large'], 'standard');
  var settings = document.querySelector('.reading-settings');
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && settings.open) {
      settings.open = false;
      settings.querySelector('summary').focus();
    }
  });
  document.addEventListener('click', function (event) {
    if (!settings.contains(event.target)) settings.open = false;
  });
  var toc = document.querySelector('.article-toc');
  if (!toc) return;
  var headings = document.querySelectorAll('.article-content h2');
  headings.forEach(function (heading, index) {
    if (!heading.id) heading.id = 'section-' + (index + 1);
    var item = document.createElement('li');
    var link = document.createElement('a');
    link.href = '#' + heading.id;
    link.textContent = heading.textContent;
    item.appendChild(link);
    toc.querySelector('ol').appendChild(item);
  });
  toc.hidden = !headings.length;
})();
