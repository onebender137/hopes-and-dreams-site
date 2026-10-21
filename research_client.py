import os
from config import Config  # v0.9x: load_dotenv() must run BEFORE metapub import,
# or metapub reads NCBI_API_KEY before it exists in os.environ
from metapub import PubMedFetcher

class ResearchClient:
    def __init__(self):
        """Initializes the PubMed fetcher (Research tool #1) with API key to avoid rate limits."""
        # Use the API key from config if available
        self.api_key = Config.NCBI_API_KEY
        # metapub uses env var 'NCBI_API_KEY' if set
        if self.api_key:
            os.environ['NCBI_API_KEY'] = self.api_key
        self.fetcher = PubMedFetcher()

    def search_studies(self, keyword: str, limit: int = 3):
        """Searches for recent PubMed studies on a biohacking topic."""
        print(f"Searching PubMed for: {keyword}...")
        pmids = self.fetcher.pmids_for_query(keyword, retmax=limit)
        
        results = []
        for pmid in pmids:
            try:
                article = self.fetcher.article_by_pmid(pmid)
                results.append({
                    "title": article.title,
                    "pmid": pmid,
                    "doi": f"https://doi.org/{article.doi}" if article.doi else None,
                    "abstract": article.abstract or "",
                    "journal": article.journal,
                    "year": article.year
                })
            except Exception as e:
                print(f"Error fetching PubMed article {pmid}: {e}")
        
        return results

    def _ncbi_get(self, url, timeout=60, retries=3):
        """v0.9x: paced NCBI GET with retry/backoff. Keyless NCBI is 3 req/s
        and efetch is the most throttled call — a 429 is common on burst.
        Returns bytes, or None after retries exhausted."""
        import time
        import urllib.request
        import urllib.error
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(url, timeout=timeout) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    wait = 3 * (attempt + 1)
                    print(f"[PMC] 429 rate-limited; retrying in {wait}s (attempt {attempt+1}/{retries}).")
                    time.sleep(wait)
                    continue
                raise
            except Exception:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                raise
        return None

    def full_text_for_pmid(self, pmid, max_chars=30000):
        """v0.9x: fetch the FULL paper text from PubMed Central for a PMID.

        Chain: elink (pubmed->pmc) -> efetch (pmc full XML) -> strip tags.
        Returns the body text (capped at max_chars) or None if the paper has
        no PMC full text (then the caller falls back to the abstract).
        Keyless-safe: 2 NCBI calls per paper, well under the 3 req/s limit.
        """
        import re
        import urllib.request
        import xml.etree.ElementTree as ET
        try:
            # 1. PMID -> PMC ID
            elink_url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
                         f"?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json")
            raw = self._ncbi_get(elink_url, timeout=30)
            if raw is None:
                return None
            data = __import__("json").loads(raw)
            pmc_id = None
            for ls in data.get("linksets", []):
                for ldb in ls.get("linksetdbs", []):
                    if ldb.get("linkname") == "pubmed_pmc" and ldb.get("links"):
                        pmc_id = ldb["links"][0]
                        break
                if pmc_id:
                    break
            if not pmc_id:
                return None
            # 2. PMC ID -> full-text XML
            import time as _time
            _time.sleep(0.4)  # pace: stay under 3 req/s keyless
            efetch_url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                          f"?db=pmc&id={pmc_id}&rettype=full&retmode=xml")
            xml_bytes = self._ncbi_get(efetch_url, timeout=60)
            if xml_bytes is None:
                return None
            root = ET.fromstring(xml_bytes)
            # 3. Walk the body, collect paragraph text (skip tables/figures).
            # ET.fromstring is safe here: the XML is NCBI's own efetch response
            # (trusted upstream), never user-supplied content.
            parts = []
            body = root.find(".//{http://www.w3.org/1999/xhtml}body")
            if body is None:
                body = root.find(".//body")
            if body is None:
                return None
            for p in body.iter():
                tag = p.tag.split("}")[-1]
                if tag in ("p", "title", "sec"):
                    txt = "".join(p.itertext()).strip()
                    if txt:
                        parts.append(txt)
            text = "\n\n".join(parts)
            if len(text) < 500:
                return None
            return text[:max_chars]
        except Exception as e:
            print(f"[PMC] full-text fetch failed for PMID {pmid}: {e}")
            return None

    def format_study_as_post(self, study: dict):
        """Formats a single study into a compelling Facebook post snippet."""
        if not study:
            return "No recent studies found for this topic."
            
        post = f"🔬 **NEW RESEARCH DEEP-DIVE: {study['title']}**\n\n"
        post += f"📅 **Year:** {study['year']} | 🏥 **Journal:** {study['journal']}\n\n"
        
        if study['abstract']:
            # Take the first 300 characters of the abstract to avoid a massive post
            abstract_snip = study['abstract'][:400] + "..."
            post += f"📌 **Key Insight:** {abstract_snip}\n\n"
        
        if study['doi']:
            post += f"🔗 **Full Study:** {study['doi']}\n\n"
            
        post += "Stay at the bleeding edge! #HopesAndDreams #Biohacking #Science\n"
        post += "⚠️ *Disclaimer: Not medical advice.*"
        
        return post

if __name__ == "__main__":
    # Test PubMed research
    client = ResearchClient()
    studies = client.search_studies("Magnesium L-Threonate")
    if studies:
        print(client.format_study_as_post(studies[0]))
    else:
        print("No studies found.")
