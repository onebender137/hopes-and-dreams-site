import urllib.parse
import re
from amazon_paapi import AmazonApi
from config import Config
from iherb_client import get_client as _get_iherb
from happyhippo_client import get_client as _get_hippo

class AffiliateClient:
    def __init__(self):
        """Initializes the Amazon PA-API client AND the iHerb primary-CTA client.

        iHerb is the primary affiliate (global shipping, higher commission);
        Amazon.ca remains the fallback when iHerb has no link for a keyword.
        """
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

        # iHerb primary CTA (disabled until IHERB_AFF_ID is set)
        self.iherb = _get_iherb()
        # Happy Hippo Kratom/botanicals CTA (topic-routed; disabled until HAPPYHIPPO_AFF_ID is set)
        self.hippo = _get_hippo()
        self._last_affiliate = None

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

    def primary_link(self, keyword: str):
        """Route the CTA: Kratom/botanical topics -> Happy Hippo, else iHerb, else Amazon.

        Sets _last_affiliate so primary_disclaimer() matches the chosen link.
        """
        if self.hippo.enabled and self.hippo.is_relevant(keyword):
            self._last_affiliate = "hippo"
            return self.hippo.primary_link(keyword)
        ih = self.iherb.primary_link(keyword)
        if ih:
            self._last_affiliate = "iherb"
            return ih
        self._last_affiliate = "amazon"
        return self.generate_canadian_link(keyword)

    def generate_primary_link(self, keyword: str):
        """Backward-compat: routes via primary_link (hippo -> iherb -> amazon)."""
        return self.primary_link(keyword)

    def primary_disclaimer(self):
        """FTC disclosure matching the last chosen CTA affiliate."""
        which = getattr(self, "_last_affiliate", None)
        if which == "hippo" and self.hippo.enabled:
            return self.hippo.disclaimer()
        if which == "iherb" and self.iherb.enabled:
            return self.iherb.disclaimer()
        return "As an Amazon Associate, I earn from qualifying purchases."

    def sanitize_text(self, text: str):
        """Removes any URLs that do not contain the mandatory affiliate tag."""
        if not text:
            return text

        tag = Config.AMAZON_ASSOCIATE_TAG or "hopesanddreams-20"

        # Regex to find URLs
        url_pattern = r"https?://[^\s<>\"']+" + r"|www\.[^\s<>\"']+"

        def replace_link(match):
            url = match.group(0)
            if tag in url:
                return url
            return "[REDACTED LINK]" # Or just empty string ""

        return re.sub(url_pattern, replace_link, text)

    def format_affiliate_payload(self, pitch: str, link: str, disclaimer: str = None):
        """Combines pitch, link, and the mandatory legal disclosure."""
        if disclaimer is None:
            disclaimer = self.primary_disclaimer()
        # Sanitize the pitch just in case the LLM hallucinated other links
        clean_pitch = self.sanitize_text(pitch)
        payload = f"{clean_pitch}\n\n{disclaimer}\n{link}"
        return payload

if __name__ == "__main__":
    # Test affiliate client (Amazon + iHerb)
    client = AffiliateClient()
    print("iHerb enabled:", client.iherb.enabled)
    print("primary_link('Lion's Mane'):", client.generate_primary_link("Lion's Mane"))
    print("disclaimer:", client.primary_disclaimer())
    products = client.search_products("Magnesium Glycinate")
    if products:
        print(client.format_product_as_recommendation(products[0]))
    else:
        print("No products found or API not configured.")
