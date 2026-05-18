
"""Add vitals widget under brain image in intel.html.
- HTML slot inside brain-visualizer-container
- CSS for the widget (cockpit aesthetic)
- JS to fetch empire_stats.json + animate regional bars subtly
Idempotent: aborts if already patched."""
from pathlib import Path
import sys

src = Path("intel.html")
content = src.read_text(encoding="utf-8")
original = content

if "vitals-widget" in content:
    print("❌ Already patched. Aborting.")
    sys.exit(1)

# --- EDIT 1: Inject CSS for vitals widget ---
# Add CSS just before the existing .anatomy-diagnostics-box CSS
CSS_ANCHOR = "        .anatomy-diagnostics-box {"
CSS_BLOCK = '''        /* === VITALS COCKPIT WIDGET (UNDER BRAIN) === */
        .vitals-widget {
            margin-top: 18px;
            padding: 18px 20px;
            background: rgba(11, 11, 11, 0.5);
            border: 1px dashed rgba(56, 189, 248, 0.18);
            border-radius: 12px;
            font-family: 'Courier New', Courier, monospace;
        }
        .vitals-header {
            font-size: 0.72rem;
            color: var(--neon-blue);
            font-weight: bold;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .vitals-status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 8px #22c55e;
            margin-right: 6px;
            animation: vitals-pulse 2s ease-in-out infinite;
        }
        @keyframes vitals-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .vitals-empire-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px 16px;
            margin-bottom: 16px;
            padding-bottom: 14px;
            border-bottom: 1px dashed rgba(56, 189, 248, 0.1);
        }
        .vitals-stat-label {
            font-size: 0.65rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .vitals-stat-value {
            font-size: 0.95rem;
            color: var(--neon-gold);
            font-weight: bold;
        }
        .vitals-regions-title {
            font-size: 0.65rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 10px;
        }
        .vitals-bar-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 7px;
            font-size: 0.72rem;
        }
        .vitals-bar-label {
            color: var(--text-main);
            width: 56px;
            flex-shrink: 0;
            letter-spacing: 0.5px;
        }
        .vitals-bar-track {
            flex: 1;
            height: 6px;
            background: rgba(255,255,255,0.04);
            border-radius: 3px;
            overflow: hidden;
            position: relative;
        }
        .vitals-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--neon-blue), var(--neon-gold));
            border-radius: 3px;
            transition: width 1.5s ease-in-out;
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.4);
        }
        .vitals-bar-pct {
            color: var(--neon-blue);
            width: 36px;
            text-align: right;
            font-weight: bold;
        }
        .vitals-footer {
            font-size: 0.62rem;
            color: var(--text-dim);
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px dashed rgba(56, 189, 248, 0.08);
            display: flex;
            justify-content: space-between;
            letter-spacing: 0.5px;
        }

'''
assert content.count(CSS_ANCHOR) == 1, "CSS_ANCHOR not unique"
content = content.replace(CSS_ANCHOR, CSS_BLOCK + CSS_ANCHOR, 1)

# --- EDIT 2: Inject HTML widget after .interactive-brain-wrapper closes ---
HTML_ANCHOR = '''                    </div>
                </div>
                
                <div class="anatomy-diagnostics-box" id="diagnostics-terminal-box">'''

HTML_REPLACEMENT = '''                    </div>

                    <div class="vitals-widget" id="vitals-widget">
                        <div class="vitals-header">
                            <span><span class="vitals-status-dot"></span>SYS_VITALS // EMPIRE TELEMETRY</span>
                            <span id="vitals-status-text">STREAMING</span>
                        </div>
                        <div class="vitals-empire-grid">
                            <div>
                                <div class="vitals-stat-label">Articles 7d</div>
                                <div class="vitals-stat-value" id="vitals-articles">—</div>
                            </div>
                            <div>
                                <div class="vitals-stat-label">Bus Events 7d</div>
                                <div class="vitals-stat-value" id="vitals-events">—</div>
                            </div>
                            <div>
                                <div class="vitals-stat-label">Active Bots</div>
                                <div class="vitals-stat-value" id="vitals-bots">—</div>
                            </div>
                            <div>
                                <div class="vitals-stat-label">Heartbeat</div>
                                <div class="vitals-stat-value" id="vitals-integrity">—</div>
                            </div>
                        </div>
                        <div class="vitals-regions-title">REGIONAL ACTIVITY MONITOR</div>
                        <div class="vitals-bar-row">
                            <span class="vitals-bar-label">PFC</span>
                            <div class="vitals-bar-track"><div class="vitals-bar-fill" id="bar-pfc" style="width: 73%"></div></div>
                            <span class="vitals-bar-pct" id="pct-pfc">73%</span>
                        </div>
                        <div class="vitals-bar-row">
                            <span class="vitals-bar-label">HIPPO</span>
                            <div class="vitals-bar-track"><div class="vitals-bar-fill" id="bar-hippo" style="width: 58%"></div></div>
                            <span class="vitals-bar-pct" id="pct-hippo">58%</span>
                        </div>
                        <div class="vitals-bar-row">
                            <span class="vitals-bar-label">AMYG</span>
                            <div class="vitals-bar-track"><div class="vitals-bar-fill" id="bar-amyg" style="width: 22%"></div></div>
                            <span class="vitals-bar-pct" id="pct-amyg">22%</span>
                        </div>
                        <div class="vitals-bar-row">
                            <span class="vitals-bar-label">VAGUS</span>
                            <div class="vitals-bar-track"><div class="vitals-bar-fill" id="bar-vagus" style="width: 88%"></div></div>
                            <span class="vitals-bar-pct" id="pct-vagus">88%</span>
                        </div>
                        <div class="vitals-footer">
                            <span>LAST SYNC: <span id="vitals-last-sync">--:--</span></span>
                            <span>NEXT: <span id="vitals-next-sync">15m</span></span>
                        </div>
                    </div>
                </div>
                
                <div class="anatomy-diagnostics-box" id="diagnostics-terminal-box">'''

assert content.count(HTML_ANCHOR) == 1, "HTML_ANCHOR not unique"
content = content.replace(HTML_ANCHOR, HTML_REPLACEMENT, 1)

# --- EDIT 3: Inject JS at the end of existing <script> block ---
# Find the existing closing </script> tag near the end
JS_ANCHOR = '''        function triggerBrainIntel(regionId) {'''
JS_BLOCK = '''        // === VITALS WIDGET — empire stats + subtle bar drift ===
        function fetchEmpireStats() {
            fetch('empire_stats.json?cb=' + Date.now())
                .then(res => res.json())
                .then(data => {
                    const e = data.empire || {};
                    document.getElementById('vitals-articles').textContent = e.articles_published_7d ?? '—';
                    document.getElementById('vitals-events').textContent = (e.bus_events_total_7d ?? 0).toLocaleString();
                    document.getElementById('vitals-bots').textContent = e.active_bots ?? '—';
                    document.getElementById('vitals-integrity').textContent = (e.heartbeat_integrity_pct ?? '—') + '%';
                    if (data.generated_at) {
                        const d = new Date(data.generated_at);
                        const hh = String(d.getHours()).padStart(2,'0');
                        const mm = String(d.getMinutes()).padStart(2,'0');
                        document.getElementById('vitals-last-sync').textContent = `${hh}:${mm}`;
                    }
                })
                .catch(err => {
                    document.getElementById('vitals-status-text').textContent = 'OFFLINE';
                    console.warn('empire_stats fetch failed:', err);
                });
        }

        function driftRegionalBars() {
            const regions = ['pfc', 'hippo', 'amyg', 'vagus'];
            regions.forEach(r => {
                const barEl = document.getElementById('bar-' + r);
                const pctEl = document.getElementById('pct-' + r);
                if (!barEl || !pctEl) return;
                const current = parseInt(barEl.style.width) || 50;
                // Drift ±4% per cycle, clamped 15-95
                const drift = Math.floor(Math.random() * 9) - 4;
                const next = Math.max(15, Math.min(95, current + drift));
                barEl.style.width = next + '%';
                pctEl.textContent = next + '%';
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            fetchEmpireStats();
            setInterval(fetchEmpireStats, 60000);  // refresh stats every 60s
            setInterval(driftRegionalBars, 30000);  // drift bars every 30s
        });

        ''' + JS_ANCHOR

assert content.count(JS_ANCHOR) == 1, "JS_ANCHOR not unique"
content = content.replace(JS_ANCHOR, JS_BLOCK, 1)

backup = Path("intel.html.bak-before-vitalswidget-20260517")
backup.write_text(original, encoding="utf-8")
src.write_text(content, encoding="utf-8")

print("PATCH APPLIED")
print(f"  Backup: {backup.name}")
print(f"  Old: {len(original)} bytes")
print(f"  New: {len(content)} bytes")
print(f"  Delta: +{len(content) - len(original)}")
