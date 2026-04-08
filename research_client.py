import os
from metapub import PubMedFetcher
from config import Config

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
                    "doi": f"https://doi.org/{article.doi}" if article.doi else None,
                    "abstract": article.abstract,
                    "journal": article.journal,
                    "year": article.year
                })
            except Exception as e:
                print(f"Error fetching PubMed article {pmid}: {e}")
        
        return results

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
