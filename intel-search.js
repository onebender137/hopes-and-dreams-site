/* ============================================================================
   intel-search.js  —  Syndicate Intel Search
   Dream Syndicate Digital Assets // hopes-and-dreams.ca

   Drop-in, dependency-free client-side search over the transmissions archive.

   USAGE
     1. Commit this file to the repo root.
     2. In any page <head>:  <script defer src="intel-search.js"></script>
     3. Drop a mount anywhere in the body:
            <div id="intel-search"></div>
        ...or for extra mounts on the same page:
            <div data-intel-search></div>

   OPTIONAL data-attributes on the mount element:
     data-source       index URL (default "transmissions.json")
     data-limit        max results shown (default 40)
     data-placeholder  input placeholder text
     data-label        Courier sector label above the bar
                       (default "INTEL // SEARCH ARCHIVE"; set data-label="" to hide)

   DATA SOURCE
     Prefers transmissions.json  -> [{ href, title, date }, ...]
     Falls back to scraping in-page .archive-item links if the JSON 404s,
     so it still works on transmissions.html even with no JSON deployed.

   THEME
     Injects its own scoped CSS using your existing vars
     (--neon-blue, --neon-gold, --text-main, --text-dim, --transition-speed),
     with hard fallbacks. Honours body.light-mode. You touch style.css zero times.

   KEYBOARD
     /            focus the first search box
     ArrowUp/Down move selection
     Enter        open selected (or first) result
     Esc          clear, then blur
   ============================================================================ */
(function () {
  'use strict';

  var DEFAULT_SOURCE = 'transmissions.json';
  var STYLE_ID = 'intel-search-styles';

  /* ---- tiny helpers ------------------------------------------------------ */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function escapeAttr(s) {
    return String(s).replace(/"/g, '&quot;');
  }

  /* ---- styles (scoped, uses site vars + fallbacks) ----------------------- */
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.intel-search{',
      '--is-blue:var(--neon-blue,#38bdf8);--is-gold:var(--neon-gold,#fbbf24);',
      '--is-main:var(--text-main,#e8eef2);--is-dim:var(--text-dim,#7c8a93);',
      '--is-speed:var(--transition-speed,0.3s);',
      'margin:0 0 42px;font-family:"Inter",system-ui,sans-serif;text-align:left;}',

      '.intel-search-label{font-family:"Courier New",Courier,monospace;font-size:0.78rem;',
      'color:var(--is-gold);font-weight:bold;letter-spacing:2px;text-transform:uppercase;',
      'margin:0 0 14px;display:block;}',

      '.intel-search-bar{display:flex;align-items:center;gap:12px;padding:14px 18px;',
      'background:rgba(11,11,11,0.5);border:1px dashed rgba(56,189,248,0.30);border-radius:14px;',
      'transition:border-color .2s ease,box-shadow .2s ease;box-sizing:border-box;}',
      '.intel-search-bar:focus-within{border-color:var(--is-blue);border-style:solid;',
      'box-shadow:0 0 18px rgba(56,189,248,0.18);}',

      '.intel-search-prompt{font-family:"Courier New",Courier,monospace;color:var(--is-blue);',
      'font-weight:bold;font-size:1.15rem;line-height:1;user-select:none;}',
      '.intel-search-prompt::after{content:"";display:inline-block;width:8px;height:1.05rem;',
      'margin-left:2px;background:var(--is-blue);vertical-align:-2px;opacity:0;',
      'animation:intel-blink 1.1s steps(1) infinite;}',
      '.intel-search-bar:focus-within .intel-search-prompt::after{opacity:1;}',
      '@keyframes intel-blink{0%,50%{opacity:1;}51%,100%{opacity:0;}}',

      '.intel-search-input{flex:1;background:transparent;border:none;outline:none;',
      'color:var(--is-main);font-family:"Courier New",Courier,monospace;font-size:1rem;',
      'letter-spacing:.5px;padding:2px 0;min-width:0;}',
      '.intel-search-input::placeholder{color:var(--is-dim);}',

      '.intel-search-clear{background:transparent;border:none;color:var(--is-dim);',
      'font-size:1.5rem;line-height:1;cursor:pointer;padding:0 2px;transition:color .2s;}',
      '.intel-search-clear:hover{color:var(--is-gold);}',
      '.intel-search-clear[hidden]{display:none;}',

      '.intel-search-meta{font-family:"Courier New",Courier,monospace;font-size:0.72rem;',
      'letter-spacing:1.2px;text-transform:uppercase;color:var(--is-gold);',
      'margin:16px 2px 18px;min-height:0;}',
      '.intel-search-meta:empty{margin:0;}',
      '.intel-search-meta .intel-cap,.intel-search-meta .intel-no{color:var(--is-dim);}',

      '.intel-search-results{display:flex;flex-direction:column;gap:10px;}',

      '.intel-search .intel-result{display:flex;justify-content:space-between;align-items:center;',
      'gap:14px;padding:14px 18px;background:rgba(255,255,255,0.015);',
      'border:1px solid rgba(255,255,255,0.05);border-radius:12px;text-decoration:none;',
      'transition:all var(--is-speed) ease;box-sizing:border-box;}',
      '.intel-search .intel-result:hover,.intel-search .intel-result.intel-active{',
      'background:rgba(56,189,248,0.05);border-color:var(--is-blue);',
      'box-shadow:0 0 15px rgba(56,189,248,0.12);}',
      '.intel-search .intel-result .title{color:var(--is-main);font-weight:700;font-size:1rem;',
      'text-transform:capitalize;line-height:1.35;}',
      '.intel-search .intel-result:hover .title,.intel-search .intel-result.intel-active .title{',
      'color:var(--is-blue);}',
      '.intel-search .intel-result .title .intel-hit{color:var(--is-gold);',
      'background:rgba(251,191,36,0.10);border-radius:3px;padding:0 2px;}',
      '.intel-search .intel-result .date{font-family:"Courier New",Courier,monospace;',
      'font-size:0.82rem;color:var(--is-dim);flex-shrink:0;}',

      '@media (max-width:600px){',
      '.intel-search .intel-result{flex-direction:column;align-items:flex-start;gap:6px;}',
      '.intel-search .intel-result .date{align-self:flex-end;}}',

      'body.light-mode .intel-search-bar{background:rgba(245,245,250,0.6);',
      'border-color:rgba(56,189,248,0.30);}',
      'body.light-mode .intel-search .intel-result{background:rgba(0,0,0,0.015);',
      'border-color:rgba(0,0,0,0.06);}'
    ].join('');
    var el = document.createElement('style');
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  /* ---- data load: prefer JSON, fall back to in-DOM archive items --------- */
  var _cache = null;
  var _loading = null;

  function normalize(arr) {
    if (!Array.isArray(arr)) return [];
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      var a = arr[i] || {};
      var title = (a.title || '').trim();
      var href = (a.href || '').trim();
      if (!title || !href) continue;
      out.push({ href: href, title: title, date: (a.date || '').trim(), _t: title.toLowerCase() });
    }
    return out;
  }

  function scrapeDom() {
    var nodes = document.querySelectorAll(
      '#full-archive-list .archive-item, .intel-feed-wrapper .archive-item, .archive-list .archive-item'
    );
    var seen = {}, out = [];
    for (var i = 0; i < nodes.length; i++) {
      var a = nodes[i];
      var t = a.querySelector('.title');
      var d = a.querySelector('.date');
      var href = (a.getAttribute('href') || '').trim();
      var title = t ? t.textContent.trim() : '';
      if (!href || !title || seen[href]) continue;
      seen[href] = 1;
      out.push({ href: href, title: title, date: d ? d.textContent.trim() : '', _t: title.toLowerCase() });
    }
    return out;
  }

  function loadIndex(source) {
    if (_cache) return Promise.resolve(_cache);
    if (_loading) return _loading;
    _loading = fetch(source, { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
      .then(function (data) { _cache = normalize(data); return _cache; })
      .catch(function () { _cache = scrapeDom(); return _cache; });
    return _loading;
  }

  /* ---- search + ranking -------------------------------------------------- */
  function runSearch(index, q, limit) {
    q = q.trim().toLowerCase();
    if (!q) return [];
    var tokens = q.split(/\s+/);
    var scored = [];
    for (var i = 0; i < index.length; i++) {
      var it = index[i];
      var hay = it._t + ' ' + it.date;
      var ok = true, score = 0;
      for (var k = 0; k < tokens.length; k++) {
        var tk = tokens[k];
        var pos = hay.indexOf(tk);
        if (pos === -1) { ok = false; break; }
        if (it._t.indexOf(tk) === 0) score += 100;        // title starts with token
        else if (it._t.indexOf(' ' + tk) !== -1) score += 50; // word-boundary hit
        else if (it._t.indexOf(tk) !== -1) score += 25;   // substring in title
        else score += 5;                                  // matched only in date
        score -= pos * 0.01;                              // earlier match = better
      }
      if (ok) scored.push({ it: it, s: score });
    }
    scored.sort(function (a, b) {
      if (b.s !== a.s) return b.s - a.s;
      return (b.it.date || '').localeCompare(a.it.date || ''); // tiebreak: newer first
    });
    var out = [];
    for (var j = 0; j < scored.length && j < limit; j++) out.push(scored[j].it);
    return out;
  }

  function highlight(title, tokens) {
    if (!tokens.length) return escapeHtml(title);
    var lower = title.toLowerCase();
    var ranges = [];
    for (var t = 0; t < tokens.length; t++) {
      var tk = tokens[t];
      if (!tk) continue;
      var from = 0, idx;
      while ((idx = lower.indexOf(tk, from)) !== -1) {
        ranges.push([idx, idx + tk.length]);
        from = idx + tk.length;
      }
    }
    if (!ranges.length) return escapeHtml(title);
    ranges.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [ranges[0].slice()];
    for (var r = 1; r < ranges.length; r++) {
      var last = merged[merged.length - 1];
      if (ranges[r][0] <= last[1]) last[1] = Math.max(last[1], ranges[r][1]);
      else merged.push(ranges[r].slice());
    }
    var out = '', pos = 0;
    for (var m = 0; m < merged.length; m++) {
      out += escapeHtml(title.slice(pos, merged[m][0]));
      out += '<span class="intel-hit">' + escapeHtml(title.slice(merged[m][0], merged[m][1])) + '</span>';
      pos = merged[m][1];
    }
    out += escapeHtml(title.slice(pos));
    return out;
  }

  /* ---- mount one search instance ----------------------------------------- */
  function mount(el) {
    if (el.getAttribute('data-intel-mounted')) return;
    el.setAttribute('data-intel-mounted', '1');

    var source = el.getAttribute('data-source') || DEFAULT_SOURCE;
    var limit = parseInt(el.getAttribute('data-limit'), 10) || 40;
    var placeholder = el.hasAttribute('data-placeholder')
      ? el.getAttribute('data-placeholder') : 'search transmissions by topic, compound, date\u2026';
    var label = el.hasAttribute('data-label')
      ? el.getAttribute('data-label') : 'INTEL // SEARCH ARCHIVE';

    el.classList.add('intel-search');
    el.innerHTML =
      (label ? '<span class="intel-search-label">' + escapeHtml(label) + '</span>' : '') +
      '<div class="intel-search-bar">' +
        '<span class="intel-search-prompt">&gt;</span>' +
        '<input type="text" class="intel-search-input" autocomplete="off" spellcheck="false" ' +
          'aria-label="Search transmissions" placeholder="' + escapeAttr(placeholder) + '">' +
        '<button class="intel-search-clear" type="button" aria-label="Clear search" hidden>&times;</button>' +
      '</div>' +
      '<div class="intel-search-meta" aria-live="polite"></div>' +
      '<div class="intel-search-results" role="listbox"></div>';

    var input = el.querySelector('.intel-search-input');
    var clearBtn = el.querySelector('.intel-search-clear');
    var meta = el.querySelector('.intel-search-meta');
    var results = el.querySelector('.intel-search-results');
    var index = [];
    var sel = -1;
    var timer;

    loadIndex(source).then(function (idx) {
      index = idx;
      if (input.value) run(); // in case they typed before the index landed
    });

    function tokensOf(q) { return q.trim().toLowerCase().split(/\s+/).filter(Boolean); }

    function render(list, q) {
      sel = -1;
      if (!q.trim()) { results.innerHTML = ''; meta.innerHTML = ''; return; }
      var tokens = tokensOf(q);
      if (!list.length) {
        meta.innerHTML = '<span class="intel-no">NO TRANSMISSIONS MATCHED</span>';
        results.innerHTML = '';
        return;
      }
      meta.innerHTML =
        '<span class="intel-count">' + list.length +
        (list.length === 1 ? ' TRANSMISSION' : ' TRANSMISSIONS') + ' MATCHED</span>' +
        (list.length >= limit ? ' <span class="intel-cap">// showing first ' + limit + '</span>' : '');
      var html = '';
      for (var i = 0; i < list.length; i++) {
        var it = list[i];
        html +=
          '<a class="intel-result" role="option" tabindex="-1" data-i="' + i + '" ' +
            'href="' + escapeAttr(it.href) + '">' +
            '<span class="title">' + highlight(it.title, tokens) + '</span>' +
            '<span class="date">' + escapeHtml(it.date) + '</span>' +
          '</a>';
      }
      results.innerHTML = html;
    }

    function run() {
      var q = input.value;
      clearBtn.hidden = !q;
      if (!q.trim()) { render([], q); return; }
      render(runSearch(index, q, limit), q);
    }

    function move(d) {
      var nodes = results.querySelectorAll('.intel-result');
      if (!nodes.length) return;
      sel = (sel + d + nodes.length) % nodes.length;
      for (var i = 0; i < nodes.length; i++) nodes[i].classList.toggle('intel-active', i === sel);
      nodes[sel].scrollIntoView({ block: 'nearest' });
    }

    function openSel() {
      var nodes = results.querySelectorAll('.intel-result');
      var node = sel >= 0 ? nodes[sel] : nodes[0];
      if (node) window.location.href = node.getAttribute('href');
    }

    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(run, 80);
      clearBtn.hidden = !input.value;
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); openSel(); }
      else if (e.key === 'Escape') {
        if (input.value) { input.value = ''; run(); } else { input.blur(); }
      }
    });
    clearBtn.addEventListener('click', function () {
      input.value = ''; run(); input.focus();
    });
  }

  /* ---- boot -------------------------------------------------------------- */
  function mountAll() {
    injectStyles();
    var mounts = document.querySelectorAll('#intel-search, [data-intel-search]');
    for (var i = 0; i < mounts.length; i++) mount(mounts[i]);
    deepLink();
  }

  // deep-link: ?q=term prefills the first box; #intel-search scrolls + focuses it.
  // Lets the index.html "Decode Intel Search" button launch straight into search.
  function deepLink() {
    try {
      var firstInput = document.querySelector('.intel-search-input');
      if (!firstInput) return;
      var q = new URLSearchParams(window.location.search).get('q');
      if (q) {
        firstInput.value = q;
        firstInput.dispatchEvent(new Event('input'));
      }
      if (window.location.hash === '#intel-search') {
        var target = document.getElementById('intel-search') || firstInput.closest('.intel-search');
        if (target && target.scrollIntoView) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setTimeout(function () {
          try { firstInput.focus({ preventScroll: true }); } catch (e) { firstInput.focus(); }
        }, 350);
      }
    } catch (e) { /* deep-link is best-effort */ }
  }

  // global "/" to focus the first search box
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (e.target && e.target.tagName ? e.target.tagName : '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || (e.target && e.target.isContentEditable)) return;
    var first = document.querySelector('.intel-search-input');
    if (first) { e.preventDefault(); first.focus(); }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountAll);
  } else {
    mountAll();
  }

  // programmatic surface
  window.IntelSearch = { mountAll: mountAll, search: runSearch, loadIndex: loadIndex };
})();
