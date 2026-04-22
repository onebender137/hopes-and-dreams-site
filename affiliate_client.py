import urllib.parse
from amazon_paapi import AmazonApi
from config import Config

class AffiliateClient:
    def __init__(self):
        """Initializes the Amazon Product Advertising API client (Monetization tool #4)."""
        # Amazon requires specific credentials
        self.access_key = Config.AMAZON_ACCESS_KEY
        self.secret_key = Config.AMAZON_SECRET_KEY
        self.partner_tag = Config.AMAZON_ASSOCIATE_TAG
        self.region = Config.AMAZON_REGION

        if self.access_key and self.secret_key:
            self.api = AmazonApi(self.access_key, self.secret_key, self.partner_tag, self.region)
        else:
            self.api = None
            print("Amazon Affiliate API not configured. Affiliate features will be disabled.")

    def search_products(self, keyword: str, limit: int = 3):
        """Searches for Amazon products matching a keyword."""
        if not self.api:
            return []

        print(f"Searching Amazon for: {keyword}...")
        try:
            results = self.api.search_items(keywords=keyword, item_count=limit)
            products = []
            for item in results.items:
                products.append({
                    "title": item.item_info.title.display_value,
                    "url": item.detail_page_url,
                    "price": item.offers.listings[0].price.display_amount if item.offers else "Check Price",
                    "image": item.images.primary.large.url if item.images else None
                })
            return products
        except Exception as e:
            print(f"Error searching Amazon: {e}")
            return []

    def format_product_as_recommendation(self, product: dict):
        """Formats a product into a compelling social media recommendation."""
        if not product:
            return "No products found for this topic."

        rec = f"💊 **HIGH-QUALITY RECOMMENDATION: {product['title']}**\n\n"
        rec += f"💰 **Price:** {product['price']}\n\n"
        rec += "This is one of the highest-rated supplements for this stack! "
        rec += "Grab it here and support the Hopes and Dreams empire:\n"
        rec += f"🔗 {product['url']}\n\n"
        rec += "#AffiliateLink #HopesAndDreams #Supplements #Biohacking"

        return rec

    def generate_canadian_link(self, keyword: str):
        """Generates a manual Amazon.ca search link with the Associate tag."""
        encoded_keyword = urllib.parse.quote_plus(keyword)
        tag = Config.AMAZON_ASSOCIATE_TAG or "hopesanddreams-20"
        return f"https://www.amazon.ca/s?k={encoded_keyword}&tag={tag}"

    def format_affiliate_payload(self, pitch: str, link: str):
        """Combines pitch, link, and the mandatory legal disclaimer."""
        disclaimer = "As an Amazon Associate, I earn from qualifying purchases."
        payload = f"{pitch}\n\n🔍 Check it out here: {link}\n\n{disclaimer}"
        return payload

if __name__ == "__main__":
    # Test Amazon Affiliate
    client = AffiliateClient()
    products = client.search_products("Magnesium Glycinate")
    if products:
        print(client.format_product_as_recommendation(products[0]))
    else:
        print("No products found or API not configured.")
