/* ============================================================================
   shop-intel.js  —  Syndicate Shop // Intel Scan Buttons
   Dream Syndicate Digital Assets // hopes-and-dreams.ca

   Auto-injects a cyberpunk "SCAN INTEL" button under the Amazon buy-button of
   every .item-card on the shop. The button deep-links into the transmissions
   Intel Search, pre-loaded with that product's compound:
       transmissions.html?q=<compound>#intel-search
   (intel-search.js on that page reads ?q= + #intel-search and opens focused.)

   USAGE
     1. Commit this file to the repo root.
     2. In shop.html <head>:  <script defer src="shop-intel.js"></script>
     That's it — works for every current AND future product card. No per-card edits.

   QUERY
     Defaults to a cleaned version of the card's <h3> (drops dosages, parentheticals,
     filler like "powder/capsules"). Override on any card for precision:
         <div class="item-card" data-product="nalt" data-intel="tyrosine">
     A data-intel value always wins. Empty derived query -> no button injected.

   THEME
     Injects its own scoped CSS off your existing vars (--neon-blue/--neon-gold),
     with fallbacks. Honours body.light-mode and prefers-reduced-motion.
     You touch style.css zero times.
   ============================================================================ */
(function () {
  'use strict';

  var STYLE_ID = 'shop-intel-styles';
  var DEST = 'transmissions.html';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.intel-scan-btn{position:relative;display:flex;align-items:center;justify-content:center;',
      'gap:9px;width:100%;margin-top:9px;padding:10px 14px;box-sizing:border-box;',
      'background:rgba(56,189,248,0.045);border:1px solid rgba(56,189,248,0.55);',
      'color:var(--neon-blue,#38bdf8);font-family:"Courier New",Courier,monospace;',
      'font-size:0.72rem;font-weight:bold;letter-spacing:2.5px;text-transform:uppercase;',
      'text-decoration:none;overflow:hidden;cursor:pointer;',
      'clip-path:polygon(7px 0,100% 0,100% calc(100% - 7px),calc(100% - 7px) 100%,0 100%,0 7px);',
      'transition:color .25s ease,border-color .25s ease,background .25s ease,box-shadow .25s ease;}',

      '.intel-scan-btn::before{content:"";position:absolute;top:0;left:-120%;width:55%;height:100%;',
      'background:linear-gradient(90deg,transparent,rgba(56,189,248,0.35),transparent);',
      'transform:skewX(-18deg);transition:left .55s ease;pointer-events:none;}',

      '.intel-scan-btn:hover{color:var(--neon-gold,#fbbf24);border-color:var(--neon-gold,#fbbf24);',
      'background:rgba(251,191,36,0.06);',
      'box-shadow:0 0 16px rgba(56,189,248,0.22),inset 0 0 12px rgba(56,189,248,0.06);',
      'text-shadow:0 0 7px rgba(251,191,36,0.55);}',
      '.intel-scan-btn:hover::before{left:140%;}',
      '.intel-scan-btn:active{transform:translateY(1px);}',
      '.intel-scan-btn:focus-visible{outline:none;border-color:var(--neon-gold,#fbbf24);',
      'box-shadow:0 0 0 2px rgba(251,191,36,0.4);}',

      '.intel-scan-reticle{font-size:0.95rem;line-height:1;',
      'animation:intel-scan-pulse 2.2s ease-in-out infinite;}',
      '.intel-scan-caret{width:7px;height:0.78rem;background:currentColor;display:inline-block;',
      'vertical-align:-1px;animation:intel-scan-blink 1.05s steps(1) infinite;}',
      '@keyframes intel-scan-pulse{0%,100%{opacity:.55;}50%{opacity:1;}}',
      '@keyframes intel-scan-blink{0%,55%{opacity:1;}56%,100%{opacity:0;}}',

      'body.light-mode .intel-scan-btn{background:rgba(56,189,248,0.07);}',

      '@media (prefers-reduced-motion: reduce){',
      '.intel-scan-btn::before,.intel-scan-reticle,.intel-scan-caret{animation:none;transition:none;}}'
    ].join('');
    var el = document.createElement('style');
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  function deriveQuery(card) {
    if (card.hasAttribute('data-intel')) {
      var v = (card.getAttribute('data-intel') || '').trim();
      return v || null;                    // data-intel="" explicitly suppresses the button
    }
    var h3 = card.querySelector('h3');
    var raw = (h3 ? h3.textContent : (card.getAttribute('data-product') || '')) || '';
    var s = raw
      .replace(/\([^)]*\)/g, ' ')                                              // (parentheticals)
      .replace(/[\d.]+\s*(mg|mcg|g|kg|fu|iu|ml|billion|cfu)\b/gi, ' ')         // dosages
      .replace(/\bstep\s*\d+\b/gi, ' ')                                        // "Step 3"
      .replace(/\b(mushroom|powder|capsules?|tablets?|patches?|extract|supplement|complex|blend)\b/gi, ' ') // filler
      .replace(/['\u2019`]/g, '')                                             // apostrophes -> Lions
      .replace(/[^\w\s\-+]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    var words = s.split(' ').filter(Boolean);
    return words.slice(0, 2).join(' ');                                        // keep it tight for the AND-match
  }

  function buildButton(query) {
    var a = document.createElement('a');
    a.className = 'intel-scan-btn';
    a.href = DEST + '?q=' + encodeURIComponent(query) + '#intel-search';
    a.setAttribute('aria-label', 'Scan the intel archive for ' + query);
    a.innerHTML =
      '<span class="intel-scan-reticle" aria-hidden="true">\u2316</span>' +
      'SCAN INTEL' +
      '<span class="intel-scan-caret" aria-hidden="true"></span>';
    return a;
  }

  function run() {
    injectStyles();
    var cards = document.querySelectorAll('.item-card');
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      if (card.getAttribute('data-intel-scan')) continue;       // already done
      var buyBtn = card.querySelector('.buy-btn');              // the Amazon link
      if (!buyBtn) continue;
      var q = deriveQuery(card);
      if (!q) continue;                                         // nothing useful to search
      card.setAttribute('data-intel-scan', '1');
      buyBtn.insertAdjacentElement('afterend', buildButton(q)); // sits directly under Amazon btn
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }

  window.ShopIntel = { run: run, deriveQuery: deriveQuery };
})();
