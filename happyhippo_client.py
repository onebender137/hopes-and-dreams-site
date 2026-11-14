"""Happy Hippo affiliate client -- Kratom/botanicals CTA for the Hopes & Dreams lane.

Why this exists
---------------
Happy Hippo is a Kratom + botanicals shop (40% commission on new customers,
10% on returning, ~$100 AOV). It is TOPIC-ROUTED, not a global primary:
Kratom / mitragynine topics go to Happy Hippo; every other supplement topic
stays on iHerb (the existing global primary). Amazon.ca remains the ultimate
fallback when neither affiliate id is set.

Design / deploy-safety
----------------------
- HAPPYHIPPO_AFF_ID is the affiliate tracking code (read from
  Config.HAPPYHIPPO_AFF_ID, falling back to the HAPPYHIPPO_AFF_ID env var).
  Happy Hippo product URLs carry it as ?sacode=<code>.
- When HAPPYHIPPO_AFF_ID is SET AND the topic is a Kratom topic: links get
  ?sacode=<code> appended and Happy Hippo is the CTA for that article.
- When HAPPYHIPPO_AFF_ID is UNSET (or the topic is not Kratom): the client is
  bypassed and the caller falls through to iHerb / Amazon (existing behavior).
  So this file is safe to deploy BEFORE the code lands -- nothing changes until
  the code is set + the services restart.
- The product map (happyhippo_products.json) links each Kratom strain/topic
  name to a specific product URL (no sacode baked in). Unmapped Kratom topics
  fall back to the /collections/buy-kratom landing page (never a dead link).
"""
import json
import os
import re
import urllib.parse
from pathlib import Path

BASE = "https://happyhippo.com"
_COLLECTION = "/collections/buy-kratom"
_MAP_FILE = Path(__file__).parent / "happyhippo_products.json"

# Keywords that mark a topic as Kratom (so affiliate_client routes it here).
# mitragynine / 7-hydroxymitragynine are Kratom's alkaloids and appear in the
# site's topic->molecule map; the region names (Maeng Da, Bali, Sumatra, ...)
# are effectively Kratom-only in this bot's topic space.
_KRATOM_TOKENS = (
    "kratom", "mitragynine", "mitragyna", "hydroxymitragynine",
    "maeng da", "bali", "sumatra", "borneo", "sundanese", "kali",
    "horn", "malay", "thai",
    "red vein", "green vein", "white vein", "yellow vein",
)


def _norm(s):
    """Normalize a name for map lookup (lowercase, alnum, single spaces)."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class HappyHippoClient:
    def __init__(self, aff_id=None, map_path=None):
        if aff_id is None:
            try:
                from config import Config
                aff_id = getattr(Config, "HAPPYHIPPO_AFF_ID", "")
            except Exception:
                aff_id = ""
        if not aff_id:
            aff_id = os.getenv("HAPPYHIPPO_AFF_ID", "")
        self.aff_id = (aff_id or "").strip()
        self._map = self._load(map_path or _MAP_FILE)

    @property
    def enabled(self):
        return bool(self.aff_id)

    def _load(self, path):
        try:
            with open(path) as f:
                data = json.load(f)
            return {_norm(k): v for k, v in data.items() if v}
        except Exception as e:
            print(f"[HappyHippo] product map not loaded ({path}): {e}")
            return {}

    def _with_aff(self, url):
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}sacode={self.aff_id}"

    def is_relevant(self, keyword):
        """True when the topic is a Kratom/botanical topic we should route here."""
        key = _norm(keyword)
        if not key:
            return False
        return any(_norm(tok) in key for tok in _KRATOM_TOKENS)

    def _match(self, keyword):
        """Return a mapped product URL for keyword (exact, then longest containment)."""
        key = _norm(keyword)
        if key in self._map:
            return self._map[key]
        best = None
        for k, v in self._map.items():
            if not k:
                continue
            if k in key or key in k:
                if best is None or len(k) > len(best[0]):
                    best = (k, v)
        return best[1] if best else None

    def product_link(self, keyword):
        """Direct product link from the map, or None if unmapped/disabled."""
        if not self.enabled:
            return None
        url = self._match(keyword)
        return self._with_aff(url) if url else None

    def collection_link(self):
        """The /collections/buy-kratom landing page (universal Kratom fallback)."""
        if not self.enabled:
            return None
        return f"{BASE}{_COLLECTION}?sacode={self.aff_id}"

    def primary_link(self, keyword):
        """Kratom product link, else the collection landing page, else None."""
        return self.product_link(keyword) or self.collection_link()

    def disclaimer(self):
        return "As a Happy Hippo affiliate, I may earn a commission from qualifying purchases."


_CLIENT = None


def get_client():
    """Module-level singleton (aff_id read at construction; restart picks up changes)."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = HappyHippoClient()
    return _CLIENT
