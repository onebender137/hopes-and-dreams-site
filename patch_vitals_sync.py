"""Sync regional bars with brain region selection.
- Active region: 80-95% with small drift
- Inactive regions: 25-55% with small drift
- Region change: smooth ~2s rebalance
- Idle (no selection): original wide-range drift behavior preserved as fallback
Idempotent: aborts if already patched."""
from pathlib import Path
import sys

src = Path("intel.html")
content = src.read_text(encoding="utf-8")
original = content

if "activeRegionId" in content:
    print("❌ Already patched. Aborting.")
    sys.exit(1)

# Replace the old driftRegionalBars + add activeRegionId state
OLD_JS = '''        function driftRegionalBars() {
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
        }'''

NEW_JS = '''        let activeRegionId = null;  // tracks which brain region is currently selected

        function driftRegionalBars() {
            const regions = ['pfc', 'hippo', 'amyg', 'vagus'];
            regions.forEach(r => {
                const barEl = document.getElementById('bar-' + r);
                const pctEl = document.getElementById('pct-' + r);
                if (!barEl || !pctEl) return;
                const current = parseInt(barEl.style.width) || 50;
                let next;
                if (activeRegionId === r) {
                    // Active region: pulse high, 80-95% with ±3% drift
                    const drift = Math.floor(Math.random() * 7) - 3;
                    next = Math.max(80, Math.min(95, current + drift));
                } else if (activeRegionId) {
                    // Inactive regions while another is active: low baseline 25-55%
                    const drift = Math.floor(Math.random() * 7) - 3;
                    next = Math.max(25, Math.min(55, current + drift));
                } else {
                    // No selection: original wide-range idle drift 15-95%
                    const drift = Math.floor(Math.random() * 9) - 4;
                    next = Math.max(15, Math.min(95, current + drift));
                }
                barEl.style.width = next + '%';
                pctEl.textContent = next + '%';
            });
        }

        function syncBarsToRegion(regionId) {
            // Called from triggerBrainIntel — rebalances bars to the new active region
            activeRegionId = regionId;
            const regions = ['pfc', 'hippo', 'amyg', 'vagus'];
            regions.forEach(r => {
                const barEl = document.getElementById('bar-' + r);
                const pctEl = document.getElementById('pct-' + r);
                if (!barEl || !pctEl) return;
                let target;
                if (r === regionId) {
                    target = 85 + Math.floor(Math.random() * 8);  // 85-92%
                } else {
                    target = 28 + Math.floor(Math.random() * 22);  // 28-50%
                }
                barEl.style.width = target + '%';
                pctEl.textContent = target + '%';
            });
        }'''

assert content.count(OLD_JS) == 1, "OLD_JS anchor not unique"
content = content.replace(OLD_JS, NEW_JS, 1)

# Hook syncBarsToRegion into triggerBrainIntel — add as first line of function body
TRIGGER_ANCHOR = '''        function triggerBrainIntel(regionId) {
            document.querySelectorAll('.brain-svg-hotspot').forEach(node => {
                node.classList.remove('active-target');
            });'''

TRIGGER_REPLACEMENT = '''        function triggerBrainIntel(regionId) {
            syncBarsToRegion(regionId);
            document.querySelectorAll('.brain-svg-hotspot').forEach(node => {
                node.classList.remove('active-target');
            });'''

assert content.count(TRIGGER_ANCHOR) == 1, "TRIGGER_ANCHOR not unique"
content = content.replace(TRIGGER_ANCHOR, TRIGGER_REPLACEMENT, 1)

backup = Path("intel.html.bak-before-vitalsync-20260517")
backup.write_text(original, encoding="utf-8")
src.write_text(content, encoding="utf-8")

print("PATCH APPLIED")
print(f"  Backup: {backup.name}")
print(f"  Old: {len(original)} bytes")
print(f"  New: {len(content)} bytes")
print(f"  Delta: +{len(content) - len(original)}")
