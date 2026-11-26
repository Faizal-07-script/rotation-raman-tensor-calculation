/* Translate the interface without reloading or changing a calculation. */
(() => {
  'use strict';
  const locales = ['id', 'zh-Hant-TW', 'ja', 'ta'];
  const supported = new Set(['en', ...locales]);
  const catalog = window.RAMAN_TRANSLATIONS;
  const phrases = new Map(Object.entries(catalog).map(([source, target]) => [source.toLowerCase(), target]));
  const key = 'raman-v5-language';
  const attributes = ['alt', 'aria-label', 'label', 'placeholder', 'title'];
  const ignored = 'script, style, pre, code, math, .katex, [data-tex], [data-no-localize]';
  const originalText = new WeakMap();
  const originalAttrs = new WeakMap();
  const selector = document.getElementById('site-language');
  let locale = 'en';

  function lookup(value, column) {
    return phrases.get(value.toLowerCase())?.[column];
  }

  function translate(value, language = locale) {
    const column = locales.indexOf(language);
    if (column < 0 || typeof value !== 'string') return value;
    const word = value.trim().replace(/\s+/g, ' ');
    if (!word) return value;
    let translated = lookup(word, column);
    if (!translated) {
      const decorated = word.match(/^([←↑↓↗→]\s*)?(\d+(?:\.\d+)*\.?\s+)?(.+?)(\s*[←↑↓↗→])?$/);
      if (decorated) {
        const [, icon, number, body, tail] = decorated;
        const label = lookup(body, column);
        if (label) translated = (icon || '') + (number || '') + label + (tail || '');
      }
    }
    if (!translated) {
      const cell = word.match(/^Cell (\d+)(\s*[·:—-]\s*(.+))?$/);
      if (cell) {
        const title = cell[3] && lookup(cell[3], column);
        translated = lookup('Cell', column) + ' ' + cell[1]
          + (title ? cell[2].slice(0, -cell[3].length) + title : (cell[2] || ''));
      }
    }
    if (!translated && /(?: · | \/ )/.test(word)) {
      const segments = word.split(/( · | \/ )/);
      const labels = segments.map(piece => translate(piece, language));
      if (labels.some((piece, i) => piece !== segments[i])) translated = labels.join('');
    }
    if (!translated) {
      const error = word.match(/^Enter a finite number for (.+)\.$/);
      if (error) translated = lookup('Enter a finite number for {field}.', column)?.replace('{field}', translate(error[1], language));
    }
    return translated ? value.replace(/\S(?:[\s\S]*\S)?/, () => translated) : value;
  }

  function localizeText(node) {
    const parent = node.parentElement;
    if (!parent || parent.closest(ignored)) return;
    // An option without a value uses its text as the option value.
    if (parent.tagName === 'OPTION' && !parent.hasAttribute('value')) return;
    const current = node.data;
    const previous = originalText.get(node);
    const source = previous?.display === current ? previous.source : current;
    const display = translate(source);
    if (display !== current || previous) originalText.set(node, {source, display});
    if (display !== current) node.data = display;
  }

  function localizeAttributes(element) {
    if (element.closest(ignored)) return;
    let records = originalAttrs.get(element);
    for (const attribute of attributes) {
      if (attribute === 'label' && element.tagName !== 'OPTGROUP') continue;
      const current = element.getAttribute(attribute);
      if (current === null) {
        records?.delete(attribute);
        continue;
      }
      const previous = records?.get(attribute);
      const source = previous?.display === current ? previous.source : current;
      const display = translate(source);
      if (display !== current || previous) {
        if (!records) originalAttrs.set(element, records = new Map());
        records.set(attribute, {source, display});
      }
      if (display !== current) element.setAttribute(attribute, display);
    }
  }

  function localize(root) {
    if (root.nodeType === Node.TEXT_NODE) return localizeText(root);
    if (root.nodeType !== Node.ELEMENT_NODE || root.closest(ignored)) return;
    localizeAttributes(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        return node.nodeType === Node.ELEMENT_NODE && node.matches(ignored)
          ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      }
    });
    while (walker.nextNode()) {
      const child = walker.currentNode;
      if (child.nodeType === Node.TEXT_NODE) localizeText(child);
      else localizeAttributes(child);
    }
  }

  function setLanguage(language, save = true) {
    if (!supported.has(language)) language = 'en';
    locale = language;
    document.documentElement.lang = language;
    selector.value = language;
    if (save) {
      try { localStorage.setItem(key, language); } catch {}
    }
    localize(document.querySelector('title'));
    localize(document.body);
    document.dispatchEvent(new CustomEvent('raman:language-change', {detail: {language}}));
  }

  window.RamanLocale = {translate, language: () => locale};
  let initial = 'en';
  try { initial = localStorage.getItem(key) || 'en'; } catch {}
  setLanguage(initial, false);
  selector.addEventListener('change', () => setLanguage(selector.value));
  window.addEventListener('storage', event => {
    if (event.key === key && (event.newValue || 'en') !== locale) setLanguage(event.newValue, false);
  });
  const observer = new MutationObserver(changes => {
    const pending = new Set();
    for (const change of changes) {
      if (change.type === 'attributes') localizeAttributes(change.target);
      else if (change.type === 'characterData') localizeText(change.target);
      else for (const node of change.addedNodes) pending.add(node);
    }
    for (const node of pending) if (node.isConnected) localize(node);
  });
  observer.observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: attributes});
  observer.observe(document.querySelector('title'), {subtree: true, childList: true, characterData: true});
})();
