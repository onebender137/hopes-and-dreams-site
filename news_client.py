import feedparser
from config import Config

class NewsClient:
    def __init__(self):
        """Initializes the RSS news feed parser (News Desk tool #5)."""
        self.feeds = [
            "https://www.scitechdaily.com/category/medicine/feed/",
            "https://medicalxpress.com/rss-feed/health-news/",
            "https://www.sciencedaily.com/rss/health_medicine.xml",
            "https://www.nature.com/news.rss"
        ]

    def get_latest_news(self, keyword="biohacking", limit=5):
        """Fetches latest news from medical RSS feeds matching a keyword."""
        print(f"Checking news feeds for keyword: {keyword}...")
        results = []
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if keyword.lower() in entry.title.lower() or keyword.lower() in entry.description.lower():
                        results.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.published if hasattr(entry, 'published') else 'Recent',
                            "summary": entry.description[:300] + "..." if hasattr(entry, 'description') else "No summary available."
                        })
                        if len(results) >= limit:
                            return results
            except Exception as e:
                print(f"Error parsing feed {url}: {e}")
        
        return results

    def format_news_for_telegram(self, news: list):
        """Formats news results for a Telegram update."""
        if not news:
            return "No recent biohacking news found today. Check back tomorrow!"
            
        update = "📰 **BIOHACKING NEWS ROUNDUP**\n\n"
        for item in news:
            update += f"🔹 **{item['title']}**\n"
            update += f"🔗 {item['link']}\n\n"
            
        update += "Stay at the bleeding edge! #HopesAndDreams #NewsDesk"
        return update

if __name__ == "__main__":
    # Test News Desk
    client = NewsClient()
    news = client.get_latest_news("supplement")
    if news:
        print(client.format_news_for_telegram(news))
    else:
        print("No news found.")
