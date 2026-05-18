"""Add calendar 2-pane view to transmissions.html.
- Hides existing bot-maintained archive list (kept for SEO)
- Adds calendar + day-articles UI fetching from transmissions.json
- Bot's update markers untouched
Idempotent: aborts if already patched."""
from pathlib import Path
import sys

src = Path("transmissions.html")
content = src.read_text(encoding="utf-8")
original = content

if "transmissions-calendar-shell" in content:
    print("❌ Already patched. Aborting.")
    sys.exit(1)

# --- EDIT 1: Add CSS for calendar before .archive-list CSS ---
CSS_ANCHOR = "        .archive-list {"
CSS_BLOCK = '''        /* === TRANSMISSIONS CALENDAR === */
        .transmissions-calendar-shell {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
            gap: 30px;
            margin-bottom: 60px;
        }
        @media (max-width: 768px) {
            .transmissions-calendar-shell { grid-template-columns: 1fr; }
        }
        .calendar-pane, .day-articles-pane {
            background: rgba(11, 11, 11, 0.5);
            border: 1px dashed rgba(56, 189, 248, 0.18);
            border-radius: 14px;
            padding: 22px;
        }
        .calendar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            font-family: 'Courier New', Courier, monospace;
        }
        .calendar-month-title {
            color: var(--neon-gold);
            font-size: 1rem;
            font-weight: bold;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }
        .calendar-nav-btn {
            background: transparent;
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--neon-blue);
            cursor: pointer;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            padding: 4px 12px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        .calendar-nav-btn:hover {
            background: rgba(56, 189, 248, 0.1);
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 6px;
        }
        .calendar-dow {
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.65rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 0;
            border-bottom: 1px dashed rgba(255,255,255,0.05);
            margin-bottom: 4px;
        }
        .calendar-day {
            aspect-ratio: 1 / 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            color: var(--text-dim);
            border-radius: 8px;
            background: rgba(255,255,255,0.01);
            cursor: default;
            position: relative;
            transition: all 0.2s ease;
        }
        .calendar-day.empty { visibility: hidden; }
        .calendar-day.has-articles {
            color: var(--text-main);
            cursor: pointer;
            background: rgba(56, 189, 248, 0.04);
            border: 1px solid rgba(56, 189, 248, 0.15);
        }
        .calendar-day.has-articles:hover {
            background: rgba(56, 189, 248, 0.1);
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
        }
        .calendar-day.today {
            border: 1.5px solid var(--neon-blue);
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.35);
        }
        .calendar-day.selected {
            background: rgba(251, 191, 36, 0.12);
            border: 1.5px solid var(--neon-gold);
            color: var(--neon-gold);
            font-weight: bold;
        }
        .calendar-day-count {
            position: absolute;
            top: 3px;
            right: 4px;
            font-size: 0.55rem;
            color: var(--neon-gold);
            font-weight: bold;
        }
        .day-articles-header {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.78rem;
            color: var(--neon-blue);
            font-weight: bold;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .day-articles-date {
            color: var(--text-main);
            font-size: 1.3rem;
            font-weight: 900;
            margin-bottom: 18px;
            text-transform: uppercase;
        }
        .day-articles-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .day-article-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 10px;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .day-article-card:hover {
            background: rgba(56, 189, 248, 0.04);
            border-color: var(--neon-blue);
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.15);
        }
        .day-article-card .title {
            color: var(--text-main);
            font-weight: 600;
            font-size: 0.95rem;
            text-transform: capitalize;
        }
        .day-article-card:hover .title { color: var(--neon-blue); }
        .day-articles-empty {
            color: var(--text-dim);
            font-style: italic;
            text-align: center;
            padding: 30px 10px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
        }

'''
assert content.count(CSS_ANCHOR) == 1, "CSS_ANCHOR not unique"
content = content.replace(CSS_ANCHOR, CSS_BLOCK + CSS_ANCHOR, 1)

# --- EDIT 2: Inject calendar shell + hide existing archive list ---
HTML_ANCHOR = '<div class="archive-list" id="full-archive-list">'
HTML_REPLACEMENT = '''<div class="transmissions-calendar-shell">
    <div class="calendar-pane">
        <div class="calendar-header">
            <button class="calendar-nav-btn" id="cal-prev" aria-label="Previous month">← PREV</button>
            <div class="calendar-month-title" id="cal-month-title">—</div>
            <button class="calendar-nav-btn" id="cal-next" aria-label="Next month">NEXT →</button>
        </div>
        <div class="calendar-grid" id="cal-grid"></div>
    </div>
    <div class="day-articles-pane">
        <div class="day-articles-header">SYS_TRANSMISSIONS // DAILY READOUT</div>
        <div class="day-articles-date" id="day-articles-date">—</div>
        <div class="day-articles-list" id="day-articles-list"></div>
    </div>
</div>

<div class="archive-list" id="full-archive-list" style="display:none">'''

assert content.count(HTML_ANCHOR) == 1, "HTML_ANCHOR not unique"
content = content.replace(HTML_ANCHOR, HTML_REPLACEMENT, 1)

# --- EDIT 3: Inject JS before </body> ---
JS_ANCHOR = "</body>"
JS_BLOCK = '''<script>
(function() {
    const MONTH_NAMES = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    const DOW_NAMES = ['SUN','MON','TUE','WED','THU','FRI','SAT'];

    let articlesByDate = {};   // { 'YYYY-MM-DD': [{href,title,date}, ...] }
    let viewMonth = null;       // Date pointing to 1st of viewed month
    let selectedDate = null;    // 'YYYY-MM-DD'

    function pad(n) { return n < 10 ? '0' + n : '' + n; }
    function ymd(d) { return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()); }

    function fetchTransmissions() {
        return fetch('transmissions.json?cb=' + Date.now())
            .then(r => r.json())
            .then(arr => {
                articlesByDate = {};
                arr.forEach(a => {
                    if (!articlesByDate[a.date]) articlesByDate[a.date] = [];
                    articlesByDate[a.date].push(a);
                });
            })
            .catch(err => console.warn('transmissions.json fetch failed:', err));
    }

    function renderCalendar() {
        const grid = document.getElementById('cal-grid');
        const title = document.getElementById('cal-month-title');
        if (!grid || !title || !viewMonth) return;

        title.textContent = MONTH_NAMES[viewMonth.getMonth()] + ' ' + viewMonth.getFullYear();
        grid.innerHTML = '';

        // Day-of-week headers
        DOW_NAMES.forEach(d => {
            const h = document.createElement('div');
            h.className = 'calendar-dow';
            h.textContent = d;
            grid.appendChild(h);
        });

        // Pad with empty cells for days before month-start
        const firstDay = new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1);
        const startDow = firstDay.getDay();
        for (let i = 0; i < startDow; i++) {
            const e = document.createElement('div');
            e.className = 'calendar-day empty';
            grid.appendChild(e);
        }

        // Render days of the month
        const today = new Date();
        const todayStr = ymd(today);
        const lastDate = new Date(viewMonth.getFullYear(), viewMonth.getMonth()+1, 0).getDate();
        for (let d = 1; d <= lastDate; d++) {
            const dateObj = new Date(viewMonth.getFullYear(), viewMonth.getMonth(), d);
            const dateStr = ymd(dateObj);
            const cell = document.createElement('div');
            cell.className = 'calendar-day';
            cell.textContent = d;
            cell.dataset.date = dateStr;

            const hasArticles = articlesByDate[dateStr] && articlesByDate[dateStr].length > 0;
            if (hasArticles) {
                cell.classList.add('has-articles');
                const count = document.createElement('span');
                count.className = 'calendar-day-count';
                count.textContent = articlesByDate[dateStr].length;
                cell.appendChild(count);
                cell.addEventListener('click', () => selectDay(dateStr));
            }
            if (dateStr === todayStr) cell.classList.add('today');
            if (dateStr === selectedDate) cell.classList.add('selected');

            grid.appendChild(cell);
        }
    }

    function selectDay(dateStr) {
        selectedDate = dateStr;
        renderCalendar();
        renderDayArticles();
    }

    function renderDayArticles() {
        const dateEl = document.getElementById('day-articles-date');
        const listEl = document.getElementById('day-articles-list');
        if (!dateEl || !listEl) return;

        if (!selectedDate) {
            dateEl.textContent = '—';
            listEl.innerHTML = '<div class="day-articles-empty">SELECT A DAY FROM THE CALENDAR</div>';
            return;
        }

        const dateObj = new Date(selectedDate + 'T00:00:00');
        const label = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
        dateEl.textContent = label;

        const articles = articlesByDate[selectedDate] || [];
        if (articles.length === 0) {
            listEl.innerHTML = '<div class="day-articles-empty">NO TRANSMISSIONS THIS DAY</div>';
            return;
        }
        listEl.innerHTML = '';
        articles.forEach(a => {
            const card = document.createElement('a');
            card.className = 'day-article-card';
            card.href = a.href;
            const t = document.createElement('span');
            t.className = 'title';
            t.textContent = a.title;
            card.appendChild(t);
            listEl.appendChild(card);
        });
    }

    function pickInitialSelectedDate() {
        const today = new Date();
        const todayStr = ymd(today);
        if (articlesByDate[todayStr]) return todayStr;
        // fall back to most recent date with articles
        const dates = Object.keys(articlesByDate).sort().reverse();
        return dates[0] || todayStr;
    }

    document.addEventListener('DOMContentLoaded', () => {
        fetchTransmissions().then(() => {
            selectedDate = pickInitialSelectedDate();
            const sel = new Date(selectedDate + 'T00:00:00');
            viewMonth = new Date(sel.getFullYear(), sel.getMonth(), 1);
            renderCalendar();
            renderDayArticles();
        });

        document.getElementById('cal-prev').addEventListener('click', () => {
            if (!viewMonth) return;
            viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1);
            renderCalendar();
        });
        document.getElementById('cal-next').addEventListener('click', () => {
            if (!viewMonth) return;
            viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1);
            renderCalendar();
        });
    });
})();
</script>
</body>'''

assert content.count(JS_ANCHOR) == 1, "JS_ANCHOR not unique"
content = content.replace(JS_ANCHOR, JS_BLOCK, 1)

backup = Path("transmissions.html.bak-before-calendar-20260517")
backup.write_text(original, encoding="utf-8")
src.write_text(content, encoding="utf-8")

print("PATCH APPLIED")
print(f"  Backup: {backup.name}")
print(f"  Old: {len(original)} bytes")
print(f"  New: {len(content)} bytes")
print(f"  Delta: +{len(content) - len(original)}")

