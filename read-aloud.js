/* ============================================================================
   read-aloud.js  —  Syndicate Audio Transmission
   Dream Syndicate Digital Assets // hopes-and-dreams.ca

   Drop-in, dependency-free "read this to me" player for article pages.
   Uses the browser's built-in Web Speech API (speechSynthesis). No server,
   no API key, no audio files, no cost.

   USAGE
     1. Commit this file to the repo root.
     2. In the ARTICLE TEMPLATE <head>:  <script defer src="read-aloud.js"></script>
     That's it — it auto-detects the article body and injects the player above it.

     To pin it explicitly instead of auto-detecting:
            <div id="read-aloud" data-target=".article-body"></div>

   OPTIONAL data-attributes on the mount element:
     data-target       CSS selector for the article body (default: auto-detect)
     data-label        Courier sector label (default "AUDIO // TRANSMISSION";
                       set data-label="" to hide)
     data-voice        preferred voice name substring (default: best local en-*)
     data-rate         starting rate (default 1)

   HOW IT READS
     Collects block elements (p, li, h2, h3, blockquote) inside the target,
     skipping nav/aside/code/figure and the search widgets. Speaks block by
     block, highlighting the current block as it goes and scrolling it into
     view. No DOM text is rewritten — highlight is a class toggle only, so
     the article markup is never mutated.

   GOTCHAS HANDLED
     - getVoices() is async-populated -> waits on 'voiceschanged'
     - Chrome's ~15s speech cutoff -> guarded pause/resume keepalive
     - long-utterance failures -> blocks >220 chars split on sentence bounds
     - mobile autoplay policy -> first speak() happens inside the click gesture
     - speech surviving navigation -> cancel on pagehide/beforeunload
   ============================================================================ */
(function () {
  'use strict';

  var STYLE_ID = 'read-aloud-styles';
  var MAX_CHUNK = 220;

  var SUPPORTED = typeof window.speechSynthesis !== 'undefined' &&
                  typeof window.SpeechSynthesisUtterance !== 'undefined';

  /* ---- helpers ----------------------------------------------------------- */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---- styles ------------------------------------------------------------ */
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.read-aloud{',
      '--ra-blue:var(--neon-blue,#38bdf8);--ra-gold:var(--neon-gold,#fbbf24);',
      '--ra-main:var(--text-main,#e8eef2);--ra-dim:var(--text-dim,#7c8a93);',
      '--ra-speed:var(--transition-speed,0.3s);',
      'margin:0 0 34px;font-family:"Inter",system-ui,sans-serif;text-align:left;}',

      '.read-aloud-label{font-family:"Courier New",Courier,monospace;font-size:0.78rem;',
      'color:var(--ra-gold);font-weight:bold;letter-spacing:2px;text-transform:uppercase;',
      'margin:0 0 14px;display:block;}',

      '.read-aloud-bar{display:flex;align-items:center;gap:14px;padding:12px 18px;',
      'background:rgba(11,11,11,0.5);border:1px dashed rgba(56,189,248,0.30);',
      'border-radius:14px;box-sizing:border-box;flex-wrap:wrap;',
      'transition:border-color .2s ease,box-shadow .2s ease;}',
      '.read-aloud.ra-on .read-aloud-bar{border-color:var(--ra-blue);border-style:solid;',
      'box-shadow:0 0 18px rgba(56,189,248,0.18);}',

      '.read-aloud-btn{background:transparent;border:1px solid var(--ra-blue);',
      'color:var(--ra-blue);font-family:"Courier New",Courier,monospace;font-size:0.78rem;',
      'font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;',
      'border-radius:8px;padding:8px 14px;transition:all var(--ra-speed) ease;',
      'white-space:nowrap;}',
      '.read-aloud-btn:hover{background:var(--ra-blue);color:#050505;',
      'box-shadow:0 0 14px rgba(56,189,248,0.35);}',
      '.read-aloud-btn.ra-ghost{border-color:rgba(255,255,255,0.14);color:var(--ra-dim);}',
      '.read-aloud-btn.ra-ghost:hover{border-color:var(--ra-gold);background:transparent;',
      'color:var(--ra-gold);box-shadow:none;}',
      '.read-aloud-btn[hidden]{display:none;}',

      '.read-aloud-status{font-family:"Courier New",Courier,monospace;font-size:0.72rem;',
      'letter-spacing:1.2px;text-transform:uppercase;color:var(--ra-dim);',
      'margin-left:auto;white-space:nowrap;}',
      '.read-aloud.ra-on .read-aloud-status{color:var(--ra-gold);}',

      '.read-aloud-track{flex-basis:100%;height:3px;border-radius:3px;',
      'background:rgba(255,255,255,0.07);overflow:hidden;}',
      '.read-aloud-fill{height:100%;width:0;background:var(--ra-blue);',
      'box-shadow:0 0 10px rgba(56,189,248,0.6);transition:width .25s linear;}',

      /* current block highlight — class toggle only, no markup rewrite */
      '.ra-reading{background:rgba(251,191,36,0.09);',
      'box-shadow:-14px 0 0 rgba(251,191,36,0.09),14px 0 0 rgba(251,191,36,0.09);',
      'border-radius:2px;transition:background .25s ease;}',

      '@media (max-width:600px){',
      '.read-aloud-status{margin-left:0;flex-basis:100%;}}',

      'body.light-mode .read-aloud-bar{background:rgba(245,245,250,0.6);}',
      'body.light-mode .ra-reading{background:rgba(251,191,36,0.16);',
      'box-shadow:-14px 0 0 rgba(251,191,36,0.16),14px 0 0 rgba(251,191,36,0.16);}'
    ].join('');
    var el = document.createElement('style');
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  /* ---- find the article body --------------------------------------------- */
  var TARGET_GUESSES = [
    '.article-body', '.article-content', '.post-body', '.post-content',
    '.transmission-body', '.entry-content', '.content-body',
    'article .content', 'article', 'main'
  ];

  function findTarget(sel) {
    if (sel) return document.querySelector(sel);
    for (var i = 0; i < TARGET_GUESSES.length; i++) {
      var el = document.querySelector(TARGET_GUESSES[i]);
      if (el && el.querySelectorAll('p').length >= 2) return el;
    }
    return null;
  }

  var SKIP_INSIDE = 'nav,aside,footer,header,pre,code,figure,figcaption,' +
                    '.intel-search,.supp-search,.read-aloud,.archive-item,' +
                    '[data-no-read]';

  function collectBlocks(target) {
    var nodes = target.querySelectorAll('p,li,h2,h3,blockquote');
    var out = [];
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.closest(SKIP_INSIDE)) continue;
      var txt = (n.textContent || '').replace(/\s+/g, ' ').trim();
      if (txt.length < 2) continue;
      out.push({ el: n, text: txt });
    }
    return out;
  }

  /* ---- chunking: keep utterances short enough to survive ------------------ */
  function chunk(text) {
    if (text.length <= MAX_CHUNK) return [text];
    // split after . ! ? when followed by space + capital/quote — dodges
    // decimals ("0.3-1 mg") and most abbreviations
    var parts = text.split(/(?<=[.!?])\s+(?=["'\u201C]?[A-Z])/);
    var out = [], buf = '';
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      if (!buf) { buf = p; }
      else if ((buf + ' ' + p).length <= MAX_CHUNK) { buf += ' ' + p; }
      else { out.push(buf); buf = p; }
      // a single sentence longer than the cap: hard-split on commas/spaces
      while (buf.length > MAX_CHUNK * 2) {
        var cut = buf.lastIndexOf(',', MAX_CHUNK);
        if (cut < 40) cut = buf.lastIndexOf(' ', MAX_CHUNK);
        if (cut < 40) cut = MAX_CHUNK;
        out.push(buf.slice(0, cut + 1).trim());
        buf = buf.slice(cut + 1).trim();
      }
    }
    if (buf) out.push(buf);
    return out.filter(Boolean);
  }

  /* ---- voices (async-populated; must wait) -------------------------------- */
  var _voices = null;
  function getVoices() {
    if (_voices) return Promise.resolve(_voices);
    return new Promise(function (resolve) {
      var v = window.speechSynthesis.getVoices();
      if (v && v.length) { _voices = v; return resolve(v); }
      var done = false;
      function grab() {
        if (done) return;
        var vv = window.speechSynthesis.getVoices();
        if (vv && vv.length) { done = true; _voices = vv; resolve(vv); }
      }
      window.speechSynthesis.addEventListener('voiceschanged', grab);
      setTimeout(function () { done = true; resolve(_voices = (window.speechSynthesis.getVoices() || [])); }, 1500);
    });
  }

  var VOICE_PREFS = ['google us english', 'samantha', 'daniel', 'karen',
                     'microsoft aria', 'microsoft guy', 'en-us', 'en-gb'];

  function pickVoice(voices, want) {
    if (!voices || !voices.length) return null;
    var i, v;
    if (want) {
      for (i = 0; i < voices.length; i++) {
        if ((voices[i].name || '').toLowerCase().indexOf(want.toLowerCase()) !== -1) return voices[i];
      }
    }
    for (var p = 0; p < VOICE_PREFS.length; p++) {
      for (i = 0; i < voices.length; i++) {
        v = voices[i];
        var hay = ((v.name || '') + ' ' + (v.lang || '')).toLowerCase();
        if (hay.indexOf(VOICE_PREFS[p]) !== -1) return v;
      }
    }
    for (i = 0; i < voices.length; i++) {
      if ((voices[i].lang || '').toLowerCase().indexOf('en') === 0) return voices[i];
    }
    return voices[0];
  }

  /* ---- mount ------------------------------------------------------------- */
  function mount(el, target) {
    if (el.getAttribute('data-ra-mounted')) return;
    el.setAttribute('data-ra-mounted', '1');

    var label = el.hasAttribute('data-label') ? el.getAttribute('data-label') : 'AUDIO // TRANSMISSION';
    var wantVoice = el.getAttribute('data-voice') || '';
    var rate = parseFloat(el.getAttribute('data-rate')) || 1;

    el.classList.add('read-aloud');
    el.innerHTML =
      (label ? '<span class="read-aloud-label">' + escapeHtml(label) + '</span>' : '') +
      '<div class="read-aloud-bar">' +
        '<button class="read-aloud-btn ra-play" type="button">&#9654; Read to me</button>' +
        '<button class="read-aloud-btn ra-ghost ra-stop" type="button" hidden>&#9632; Stop</button>' +
        '<button class="read-aloud-btn ra-ghost ra-rate" type="button" hidden>1.0&times;</button>' +
        '<span class="read-aloud-status"></span>' +
        '<div class="read-aloud-track"><div class="read-aloud-fill"></div></div>' +
      '</div>';

    var playBtn = el.querySelector('.ra-play');
    var stopBtn = el.querySelector('.ra-stop');
    var rateBtn = el.querySelector('.ra-rate');
    var status = el.querySelector('.read-aloud-status');
    var fill = el.querySelector('.read-aloud-fill');

    var synth = window.speechSynthesis;
    var blocks = [];
    var queue = [];        // [{blockIdx, text}]
    var qi = 0;
    var totalChars = 0, doneChars = 0;
    var voice = null;
    var playing = false, paused = false;
    var keepalive = null;
    var lastHi = null;

    var RATES = [0.75, 1, 1.25, 1.5];

    function setStatus(t) { status.textContent = t; }

    function highlight(i) {
      if (lastHi) lastHi.classList.remove('ra-reading');
      lastHi = null;
      if (i < 0 || i >= blocks.length) return;
      var b = blocks[i].el;
      b.classList.add('ra-reading');
      lastHi = b;
      var r = b.getBoundingClientRect();
      if (r.top < 80 || r.bottom > window.innerHeight - 40) {
        b.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    function build() {
      blocks = collectBlocks(target);
      queue = [];
      totalChars = 0;
      for (var i = 0; i < blocks.length; i++) {
        var parts = chunk(blocks[i].text);
        for (var j = 0; j < parts.length; j++) {
          queue.push({ b: i, text: parts[j] });
          totalChars += parts[j].length;
        }
      }
      return queue.length > 0;
    }

    function startKeepalive() {
      // Chrome silently stops ~15s in; a paced pause/resume keeps it awake.
      stopKeepalive();
      keepalive = setInterval(function () {
        if (!playing || paused) return;
        if (synth.speaking) { synth.pause(); synth.resume(); }
      }, 9000);
    }
    function stopKeepalive() { if (keepalive) { clearInterval(keepalive); keepalive = null; } }

    function speakNext() {
      if (!playing) return;
      if (qi >= queue.length) { finish(); return; }
      var item = queue[qi];
      highlight(item.b);
      var u = new SpeechSynthesisUtterance(item.text);
      if (voice) { u.voice = voice; u.lang = voice.lang; }
      u.rate = rate;
      u.pitch = 1;
      u.onend = function () {
        if (!playing) return;
        doneChars += item.text.length;
        fill.style.width = Math.min(100, (doneChars / totalChars) * 100) + '%';
        qi++;
        speakNext();
      };
      u.onerror = function (e) {
        if (!playing || (e && e.error === 'interrupted')) return;
        doneChars += item.text.length;
        qi++;
        speakNext();
      };
      synth.speak(u);
    }

    function start() {
      if (!build()) { setStatus('nothing to read'); return; }
      synth.cancel();
      qi = 0; doneChars = 0;
      fill.style.width = '0%';
      playing = true; paused = false;
      el.classList.add('ra-on');
      playBtn.innerHTML = '&#10073;&#10073; Pause';
      stopBtn.hidden = false;
      rateBtn.hidden = false;
      setStatus('reading');
      startKeepalive();
      speakNext();
    }

    function finish() {
      playing = false; paused = false;
      stopKeepalive();
      synth.cancel();
      highlight(-1);
      el.classList.remove('ra-on');
      playBtn.innerHTML = '&#9654; Read to me';
      stopBtn.hidden = true;
      rateBtn.hidden = true;
      fill.style.width = '0%';
      setStatus('');
    }

    playBtn.addEventListener('click', function () {
      if (!playing) { start(); return; }        // gesture-scoped first speak (iOS)
      if (paused) {
        synth.resume(); paused = false;
        playBtn.innerHTML = '&#10073;&#10073; Pause';
        setStatus('reading');
        startKeepalive();
      } else {
        synth.pause(); paused = true;
        playBtn.innerHTML = '&#9654; Resume';
        setStatus('paused');
        stopKeepalive();
      }
    });

    stopBtn.addEventListener('click', finish);

    rateBtn.addEventListener('click', function () {
      var i = RATES.indexOf(rate);
      rate = RATES[(i + 1) % RATES.length];
      rateBtn.textContent = rate.toFixed(2).replace(/0$/, '') + '\u00D7';
      if (playing) {
        // rate only applies to new utterances — requeue from the current chunk
        synth.cancel();
        setTimeout(speakNext, 60);
      }
    });

    getVoices().then(function (vs) { voice = pickVoice(vs, wantVoice); });

    // don't let speech follow the visitor to the next page
    window.addEventListener('pagehide', function () { playing = false; stopKeepalive(); synth.cancel(); });
    window.addEventListener('beforeunload', function () { playing = false; stopKeepalive(); synth.cancel(); });
  }

  /* ---- boot -------------------------------------------------------------- */
  function mountAll() {
    if (!SUPPORTED) return;   // no player rather than a broken one
    var explicit = document.querySelector('#read-aloud, [data-read-aloud]');
    var target = findTarget(explicit ? explicit.getAttribute('data-target') : null);
    if (!target) return;      // not an article page — stay out of the way

    injectStyles();

    var el = explicit;
    if (!el) {                // auto-mount at the top of the article body
      el = document.createElement('div');
      el.id = 'read-aloud';
      target.insertBefore(el, target.firstChild);
    }
    mount(el, target);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountAll);
  else mountAll();

  window.ReadAloud = { mountAll: mountAll };
})();
