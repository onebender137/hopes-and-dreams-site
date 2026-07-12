/* ============================================================================
   supplement-search.js  —  Syndicate Nootropic / Supplement Search
   Dream Syndicate Digital Assets // hopes-and-dreams.ca

   Drop-in, dependency-free client-side compound search over the article archive.
   Sibling to intel-search.js — reuses its terminal skin + keyboard model, but
   rescoped: autocomplete over a curated compound catalog, then a supplement
   PROFILE card (what it does / dose / DYOR / shop) + the articles that ref it.

   USAGE
     1. Commit this file to the repo root.
     2. In intel.html <head>:  <script defer src="supplement-search.js"></script>
     3. Drop a mount at the top of the body:
            <div id="supplement-search"></div>          (primary)
            <div data-supplement-search></div>          (extra mounts)

   OPTIONAL data-attributes on the mount element:
     data-source       compound index URL (default "supplements.json")
     data-limit        max articles shown per compound (default 30)
     data-placeholder  input placeholder text
     data-label        Courier sector label (default "STACK // COMPOUND SEARCH";
                       set data-label="" to hide)

   DATA / LAZY LOAD
     supplements.json is NOT fetched on page load. First focus/type lazy-loads it:
       [{ name, what, dose, shop, articles:[{href,title,date}], aliases? }]
     Built by build-supplements-index.py from the existing search-index.json.

   BEHAVIOUR
     Focus (empty) -> dropdown lists the whole catalog (browsable database).
     Type          -> autocomplete filters by name + aliases (prefix-ranked).
     Select        -> profile card + article list render below.
     "/" focus, ArrowUp/Down move, Enter select/open, Esc clear-then-blur.
     Deep-link: "?s=magnesium" prefills + selects. "#supplement-search" scrolls.
   ============================================================================ */
(function () {
  'use strict';

  var DEFAULT_SOURCE = 'supplements.json';
  var STYLE_ID = 'supp-search-styles';

  /* ---- helpers ----------------------------------------------------------- */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function escapeAttr(s) { return String(s).replace(/"/g, '&quot;'); }
  function slug(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }

  /* ---- styles ------------------------------------------------------------ */
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.supp-search{',
      '--ss-blue:var(--neon-blue,#38bdf8);--ss-gold:var(--neon-gold,#fbbf24);',
      '--ss-main:var(--text-main,#e8eef2);--ss-dim:var(--text-dim,#7c8a93);',
      '--ss-speed:var(--transition-speed,0.3s);',
      'position:relative;margin:0 0 42px;font-family:"Inter",system-ui,sans-serif;text-align:left;}',

      '.supp-search-label{font-family:"Courier New",Courier,monospace;font-size:0.78rem;',
      'color:var(--ss-gold);font-weight:bold;letter-spacing:2px;text-transform:uppercase;',
      'margin:0 0 14px;display:block;}',

      '.supp-search-bar{display:flex;align-items:center;gap:12px;padding:14px 18px;',
      'background:rgba(11,11,11,0.5);border:1px dashed rgba(56,189,248,0.30);border-radius:14px;',
      'transition:border-color .2s ease,box-shadow .2s ease;box-sizing:border-box;}',
      '.supp-search-bar:focus-within{border-color:var(--ss-blue);border-style:solid;',
      'box-shadow:0 0 18px rgba(56,189,248,0.18);}',

      '.supp-search-prompt{font-family:"Courier New",Courier,monospace;color:var(--ss-blue);',
      'font-weight:bold;font-size:1.15rem;line-height:1;user-select:none;}',
      '.supp-search-prompt::after{content:"";display:inline-block;width:8px;height:1.05rem;',
      'margin-left:2px;background:var(--ss-blue);vertical-align:-2px;opacity:0;',
      'animation:supp-blink 1.1s steps(1) infinite;}',
      '.supp-search-bar:focus-within .supp-search-prompt::after{opacity:1;}',
      '@keyframes supp-blink{0%,50%{opacity:1;}51%,100%{opacity:0;}}',

      '.supp-search-input{flex:1;background:transparent;border:none;outline:none;',
      'color:var(--ss-main);font-family:"Courier New",Courier,monospace;font-size:1rem;',
      'letter-spacing:.5px;padding:2px 0;min-width:0;}',
      '.supp-search-input::placeholder{color:var(--ss-dim);}',

      '.supp-search-clear{background:transparent;border:none;color:var(--ss-dim);',
      'font-size:1.5rem;line-height:1;cursor:pointer;padding:0 2px;transition:color .2s;}',
      '.supp-search-clear:hover{color:var(--ss-gold);}',
      '.supp-search-clear[hidden]{display:none;}',

      /* ---- autocomplete dropdown ---- */
      '.supp-drop{position:absolute;left:0;right:0;z-index:40;margin-top:8px;',
      'background:rgba(9,9,11,0.97);border:1px solid var(--ss-blue);border-radius:12px;',
      'box-shadow:0 12px 34px rgba(0,0,0,0.5),0 0 18px rgba(56,189,248,0.12);',
      'max-height:340px;overflow-y:auto;padding:6px;box-sizing:border-box;}',
      '.supp-drop[hidden]{display:none;}',
      '.supp-drop-item{display:flex;align-items:baseline;gap:10px;padding:9px 12px;',
      'border-radius:8px;cursor:pointer;transition:background .12s;}',
      '.supp-drop-item:hover,.supp-drop-item.supp-active{background:rgba(56,189,248,0.10);}',
      '.supp-drop-item .supp-caret{font-family:"Courier New",Courier,monospace;color:var(--ss-blue);',
      'font-weight:bold;font-size:0.9rem;}',
      '.supp-drop-item .supp-name{color:var(--ss-main);font-weight:700;font-size:0.95rem;',
      'text-transform:capitalize;white-space:nowrap;}',
      '.supp-drop-item.supp-active .supp-name,.supp-drop-item:hover .supp-name{color:var(--ss-blue);}',
      '.supp-drop-item .supp-name .supp-hit{color:var(--ss-gold);}',
      '.supp-drop-item .supp-mini{color:var(--ss-dim);font-size:0.8rem;overflow:hidden;',
      'text-overflow:ellipsis;white-space:nowrap;}',
      '.supp-drop-item .supp-tag{margin-left:auto;font-family:"Courier New",Courier,monospace;',
      'font-size:0.68rem;color:var(--ss-dim);flex-shrink:0;letter-spacing:1px;}',

      '.supp-search-meta{font-family:"Courier New",Courier,monospace;font-size:0.72rem;',
      'letter-spacing:1.2px;text-transform:uppercase;color:var(--ss-gold);margin:16px 2px 18px;}',
      '.supp-search-meta:empty{margin:0;}',
      '.supp-search-meta .supp-dimtxt{color:var(--ss-dim);}',

      /* ---- profile card ---- */
      '.supp-profile{border:1px solid rgba(251,191,36,0.30);border-radius:14px;',
      'background:linear-gradient(180deg,rgba(251,191,36,0.04),rgba(255,255,255,0.012));',
      'padding:20px 22px;margin:0 0 22px;box-sizing:border-box;}',
      '.supp-profile-head{display:flex;justify-content:space-between;align-items:center;',
      'gap:14px;flex-wrap:wrap;margin-bottom:12px;}',
      '.supp-profile-name{font-family:"Courier New",Courier,monospace;color:var(--ss-gold);',
      'font-weight:bold;font-size:1.25rem;letter-spacing:2px;text-transform:uppercase;}',
      '.supp-profile-shop{font-family:"Courier New",Courier,monospace;font-size:0.78rem;',
      'letter-spacing:1.5px;text-transform:uppercase;color:var(--ss-blue);text-decoration:none;',
      'border:1px solid var(--ss-blue);border-radius:8px;padding:7px 14px;',
      'transition:all var(--ss-speed) ease;white-space:nowrap;}',
      '.supp-profile-shop:hover{background:var(--ss-blue);color:#050505;',
      'box-shadow:0 0 14px rgba(56,189,248,0.35);}',
      '.supp-profile-what{color:var(--ss-main);font-size:0.98rem;line-height:1.6;margin:0 0 14px;}',
      '.supp-profile-dose{font-family:"Courier New",Courier,monospace;font-size:0.9rem;',
      'color:var(--ss-main);margin:0 0 12px;}',
      '.supp-profile-dose .supp-k{color:var(--ss-blue);font-weight:bold;letter-spacing:1.5px;',
      'margin-right:10px;}',
      '.supp-profile-dose .supp-empty{color:var(--ss-dim);font-style:italic;}',
      '.supp-profile-dyor{font-family:"Courier New",Courier,monospace;font-size:0.76rem;',
      'color:var(--ss-dim);letter-spacing:0.5px;border-top:1px dashed rgba(255,255,255,0.08);',
      'padding-top:12px;margin-top:4px;}',

      /* ---- article list (mirrors intel-result) ---- */
      '.supp-articles-label{font-family:"Courier New",Courier,monospace;font-size:0.72rem;',
      'letter-spacing:1.2px;text-transform:uppercase;color:var(--ss-gold);margin:0 2px 14px;}',
      '.supp-articles-label .supp-dimtxt{color:var(--ss-dim);}',
      '.supp-articles{display:flex;flex-direction:column;gap:10px;}',
      '.supp-search .supp-result{display:flex;justify-content:space-between;align-items:center;',
      'gap:14px;padding:14px 18px;background:rgba(255,255,255,0.015);',
      'border:1px solid rgba(255,255,255,0.05);border-radius:12px;text-decoration:none;',
      'transition:all var(--ss-speed) ease;box-sizing:border-box;}',
      '.supp-search .supp-result:hover{background:rgba(56,189,248,0.05);border-color:var(--ss-blue);',
      'box-shadow:0 0 15px rgba(56,189,248,0.12);}',
      '.supp-search .supp-result .title{color:var(--ss-main);font-weight:700;font-size:1rem;',
      'text-transform:capitalize;line-height:1.35;}',
      '.supp-search .supp-result:hover .title{color:var(--ss-blue);}',
      '.supp-search .supp-result .date{font-family:"Courier New",Courier,monospace;',
      'font-size:0.82rem;color:var(--ss-dim);flex-shrink:0;}',

      '@media (max-width:600px){',
      '.supp-search .supp-result{flex-direction:column;align-items:flex-start;gap:6px;}',
      '.supp-search .supp-result .date{align-self:flex-end;}',
      '.supp-drop-item .supp-mini{display:none;}}',

      'body.light-mode .supp-search-bar{background:rgba(245,245,250,0.6);',
      'border-color:rgba(56,189,248,0.30);}',
      'body.light-mode .supp-drop{background:rgba(250,250,252,0.98);}',
      'body.light-mode .supp-search .supp-result{background:rgba(0,0,0,0.015);',
      'border-color:rgba(0,0,0,0.06);}'
    ].join('');
    var el = document.createElement('style');
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  /* ---- lazy data load ---------------------------------------------------- */
  var _cache = null;
  var _loading = null;

  function normalize(arr) {
    if (!Array.isArray(arr)) return [];
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      var c = arr[i] || {};
      var name = (c.name || '').trim();
      if (!name) continue;
      var aliases = Array.isArray(c.aliases) ? c.aliases : [];
      var terms = [name.toLowerCase()];
      for (var k = 0; k < aliases.length; k++) {
        var al = String(aliases[k] || '').toLowerCase().trim();
        if (al && terms.indexOf(al) === -1) terms.push(al);
      }
      out.push({
        name: name,
        what: (c.what || '').trim(),
        dose: (c.dose || '').trim(),
        shop: (c.shop || '').trim(),
        articles: Array.isArray(c.articles) ? c.articles : [],
        _terms: terms,
        _slug: slug(name)
      });
    }
    out.sort(function (a, b) { return a.name.toLowerCase().localeCompare(b.name.toLowerCase()); });
    return out;
  }

  function ensureData(sourceUrl) {
    if (_cache) return Promise.resolve(_cache);
    if (_loading) return _loading;
    _loading = fetch(sourceUrl, { cache: 'force-cache' })
      .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
      .then(function (d) { _cache = normalize(d); return _cache; })
      .catch(function () { _cache = []; return _cache; });
    return _loading;
  }

  /* ---- match / rank ------------------------------------------------------ */
  function rankCompounds(data, q) {
    q = q.trim().toLowerCase();
    if (!q) return data.slice();               // empty -> full browsable catalog
    var scored = [];
    for (var i = 0; i < data.length; i++) {
      var c = data[i], best = -1;
      for (var t = 0; t < c._terms.length; t++) {
        var term = c._terms[t], pos = term.indexOf(q);
        if (pos === -1) continue;
        // prefix on the primary name is strongest; alias prefix next; substring last
        var s = (t === 0 && pos === 0) ? 100 : (pos === 0 ? 80 : (t === 0 ? 55 : 40));
        if (s > best) best = s;
      }
      if (best >= 0) scored.push({ c: c, s: best });
    }
    scored.sort(function (a, b) {
      if (b.s !== a.s) return b.s - a.s;
      return a.c.name.toLowerCase().localeCompare(b.c.name.toLowerCase());
    });
    var out = [];
    for (var j = 0; j < scored.length; j++) out.push(scored[j].c);
    return out;
  }

  function highlightName(name, q) {
    q = q.trim().toLowerCase();
    if (!q) return escapeHtml(name);
    var lower = name.toLowerCase(), pos = lower.indexOf(q);
    if (pos === -1) return escapeHtml(name);
    return escapeHtml(name.slice(0, pos)) +
      '<span class="supp-hit">' + escapeHtml(name.slice(pos, pos + q.length)) + '</span>' +
      escapeHtml(name.slice(pos + q.length));
  }

  /* ---- mount ------------------------------------------------------------- */
  function mount(el) {
    if (el.getAttribute('data-supp-mounted')) return;
    el.setAttribute('data-supp-mounted', '1');

    var sourceUrl = el.getAttribute('data-source') || DEFAULT_SOURCE;
    var limit = parseInt(el.getAttribute('data-limit'), 10) || 30;
    var placeholder = el.hasAttribute('data-placeholder')
      ? el.getAttribute('data-placeholder')
      : 'search a compound\u2026 magnesium, l-theanine, ashwagandha';
    var label = el.hasAttribute('data-label') ? el.getAttribute('data-label') : 'STACK // COMPOUND SEARCH';

    el.classList.add('supp-search');
    el.innerHTML =
      (label ? '<span class="supp-search-label">' + escapeHtml(label) + '</span>' : '') +
      '<div class="supp-search-bar">' +
        '<span class="supp-search-prompt">&gt;</span>' +
        '<input type="text" class="supp-search-input" autocomplete="off" spellcheck="false" ' +
          'aria-label="Search supplements" placeholder="' + escapeAttr(placeholder) + '">' +
        '<button class="supp-search-clear" type="button" aria-label="Clear" hidden>&times;</button>' +
      '</div>' +
      '<div class="supp-drop" role="listbox" hidden></div>' +
      '<div class="supp-search-meta" aria-live="polite"></div>' +
      '<div class="supp-profile-slot"></div>' +
      '<div class="supp-articles-slot"></div>';

    var input = el.querySelector('.supp-search-input');
    var clearBtn = el.querySelector('.supp-search-clear');
    var drop = el.querySelector('.supp-drop');
    var meta = el.querySelector('.supp-search-meta');
    var profileSlot = el.querySelector('.supp-profile-slot');
    var articlesSlot = el.querySelector('.supp-articles-slot');
    var data = null;
    var current = [];   // current dropdown list
    var sel = -1;
    var timer;

    function warm() {
      if (data) return Promise.resolve(data);
      return ensureData(sourceUrl).then(function (d) { data = d; return d; });
    }

    function findByName(name) {
      var lc = name.trim().toLowerCase();
      for (var i = 0; i < (data || []).length; i++) {
        if (data[i].name.toLowerCase() === lc || data[i]._slug === slug(name)) return data[i];
      }
      return null;
    }

    function renderDrop(list, q) {
      sel = -1;
      current = list;
      if (!list.length) {
        drop.innerHTML = '<div class="supp-drop-item" style="cursor:default">' +
          '<span class="supp-mini">no compound matched \u2014 try a shorter term</span></div>';
        drop.hidden = false;
        return;
      }
      var html = '';
      for (var i = 0; i < list.length; i++) {
        var c = list[i];
        var n = c.articles ? c.articles.length : 0;
        html +=
          '<div class="supp-drop-item" role="option" data-i="' + i + '">' +
            '<span class="supp-caret">&gt;</span>' +
            '<span class="supp-name">' + highlightName(c.name, q) + '</span>' +
            (c.what ? '<span class="supp-mini">' + escapeHtml(c.what) + '</span>' : '') +
            '<span class="supp-tag">' + n + (n === 1 ? ' REF' : ' REFS') + '</span>' +
          '</div>';
      }
      drop.innerHTML = html;
      drop.hidden = false;
    }

    function closeDrop() { drop.hidden = true; sel = -1; }

    function selectCompound(c) {
      if (!c) return;
      input.value = c.name;
      clearBtn.hidden = false;
      closeDrop();

      // profile card
      var doseHtml = c.dose
        ? escapeHtml(c.dose)
        : '<span class="supp-empty">not catalogued \u2014 see articles</span>';
      profileSlot.innerHTML =
        '<div class="supp-profile">' +
          '<div class="supp-profile-head">' +
            '<span class="supp-profile-name">' + escapeHtml(c.name) + '</span>' +
            (c.shop ? '<a class="supp-profile-shop" href="' + escapeAttr(c.shop) + '">ACQUIRE \u25B8</a>' : '') +
          '</div>' +
          (c.what ? '<div class="supp-profile-what">' + escapeHtml(c.what) + '</div>' : '') +
          '<div class="supp-profile-dose"><span class="supp-k">DOSE</span>' + doseHtml + '</div>' +
          '<div class="supp-profile-dyor">// Do your own research. Don\u2019t be a statistic.</div>' +
        '</div>';

      // articles
      var arts = (c.articles || []).slice(0, limit);
      var n = (c.articles || []).length;
      if (!arts.length) {
        meta.innerHTML = '<span class="supp-dimtxt">no transmissions reference this compound yet</span>';
        articlesSlot.innerHTML = '';
        return;
      }
      meta.innerHTML = '';
      var lbl = '<div class="supp-articles-label">' + n +
        (n === 1 ? ' TRANSMISSION REFERENCES ' : ' TRANSMISSIONS REFERENCE ') + escapeHtml(c.name.toUpperCase()) +
        (n > limit ? ' <span class="supp-dimtxt">// showing first ' + limit + '</span>' : '') + '</div>';
      var html = '<div class="supp-articles">';
      for (var i = 0; i < arts.length; i++) {
        var a = arts[i] || {};
        html +=
          '<a class="supp-result" href="' + escapeAttr((a.href || '').trim()) + '">' +
            '<span class="title">' + escapeHtml((a.title || '').trim()) + '</span>' +
            '<span class="date">' + escapeHtml((a.date || '').trim()) + '</span>' +
          '</a>';
      }
      html += '</div>';
      articlesSlot.innerHTML = lbl + html;
    }

    function doFilter() {
      var q = input.value;
      clearBtn.hidden = !q;
      if (!data) {
        meta.innerHTML = '<span class="supp-dimtxt">loading catalogue\u2026</span>';
        warm().then(function () { doFilter(); });
        return;
      }
      // exact-name typed -> auto-select (e.g. deep-link or paste)
      renderDrop(rankCompounds(data, q), q);
      if (q.trim()) {
        meta.innerHTML = '';
      } else {
        meta.innerHTML = '<span class="supp-dimtxt">' + data.length + ' compounds indexed \u2014 browse or type</span>';
      }
    }

    function move(d) {
      var nodes = drop.querySelectorAll('.supp-drop-item[data-i]');
      if (!nodes.length) return;
      sel = (sel + d + nodes.length) % nodes.length;
      for (var i = 0; i < nodes.length; i++) nodes[i].classList.toggle('supp-active', i === sel);
      nodes[sel].scrollIntoView({ block: 'nearest' });
    }

    input.addEventListener('focus', function () {
      if (!data) { warm().then(function () { if (document.activeElement === input) doFilter(); }); return; }
      doFilter();
    });
    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(doFilter, 70);
      clearBtn.hidden = !input.value;
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (drop.hidden) doFilter(); else move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') {
        e.preventDefault();
        if (!drop.hidden && current.length) { selectCompound(current[sel >= 0 ? sel : 0]); }
        else { var c = findByName(input.value); if (c) selectCompound(c); }
      } else if (e.key === 'Escape') {
        if (!drop.hidden) { closeDrop(); }
        else if (input.value) { input.value = ''; profileSlot.innerHTML = ''; articlesSlot.innerHTML = ''; doFilter(); }
        else { input.blur(); }
      }
    });

    drop.addEventListener('mousedown', function (e) {
      var item = e.target.closest ? e.target.closest('.supp-drop-item[data-i]') : null;
      if (!item) return;
      e.preventDefault();
      var i = parseInt(item.getAttribute('data-i'), 10);
      if (!isNaN(i) && current[i]) selectCompound(current[i]);
    });

    clearBtn.addEventListener('click', function () {
      input.value = ''; profileSlot.innerHTML = ''; articlesSlot.innerHTML = '';
      doFilter(); input.focus();
    });

    document.addEventListener('click', function (e) {
      if (!el.contains(e.target)) closeDrop();
    });

    // expose for deep-link
    el._suppSelect = function (name) {
      warm().then(function () { var c = findByName(name); if (c) selectCompound(c); });
    };
  }

  /* ---- boot + deep-link -------------------------------------------------- */
  function deepLink() {
    try {
      var mountEl = document.querySelector('#supplement-search, [data-supplement-search]');
      if (!mountEl) return;
      var s = new URLSearchParams(window.location.search).get('s');
      if (s && mountEl._suppSelect) mountEl._suppSelect(s);
      if (window.location.hash === '#supplement-search') {
        if (mountEl.scrollIntoView) mountEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        var inp = mountEl.querySelector('.supp-search-input');
        if (inp) setTimeout(function () {
          try { inp.focus({ preventScroll: true }); } catch (e) { inp.focus(); }
        }, 350);
      }
    } catch (e) { /* best-effort */ }
  }

  function mountAll() {
    injectStyles();
    var mounts = document.querySelectorAll('#supplement-search, [data-supplement-search]');
    for (var i = 0; i < mounts.length; i++) mount(mounts[i]);
    deepLink();
  }

  document.addEventListener('keydown', function (e) {
    if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (e.target && e.target.tagName ? e.target.tagName : '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || (e.target && e.target.isContentEditable)) return;
    var first = document.querySelector('.supp-search-input');
    if (first) { e.preventDefault(); first.focus(); }
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountAll);
  else mountAll();

  window.SuppSearch = { mountAll: mountAll };
})();
