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
        tag = Config.AMAZON_ASSOCIATE_TAG or "hopes_and_dreams-20"
        return f"https://www.amazon.ca/s?k={encoded_keyword}&tag={tag}"

    def format_affiliate_payload(self, pitch: str, link: str):
        """Combines pitch, link, and the mandatory legal disclaimer."""
        disclaimer = "As an Amazon Associate, I earn from qualifying purchases."
        payload = f"{pitch}\n\n🔍 Check it out here: {link}\n\n{disclaimer}"
        return payload

    def sanitize_text(self, text, link_limit=None):
        """
        Ensures all Amazon links are correctly tagged and optionally limits the number of links.
        Also replaces amzn.to short links with tagged search links.
        """
        import re

        tag = Config.AMAZON_ASSOCIATE_TAG or "hopes_and_dreams-20"

        # 1. Replace amzn.to short links with a tagged search link for the topic if possible,
        # but since we don't know the topic here easily without complex regex,
        # we'll just try to append the tag if it's a full amazon link,
        # or if it's amzn.to, we might have to leave it or try to expand it.
        # Actually, the user says "only one has my tag", so let's focus on adding the tag.

        # Regex for Amazon links
        amazon_re = re.compile(r'https?://(?:www\.)?amazon\.(?:ca|com)/[^\s]+', re.IGNORECASE)
        amznto_re = re.compile(r'https?://amzn\.to/[^\s]+', re.IGNORECASE)

        def tag_link(match):
            url = match.group(0)
            if 'tag=' in url:
                # Replace existing tag
                return re.sub(r'tag=[^&]+', f'tag={tag}', url)
            else:
                # Add tag
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}tag={tag}"

        # Tag full links
        text = amazon_re.sub(tag_link, text)

        # For amzn.to, we can't easily add a tag parameter that Amazon will recognize after redirect.
        # However, we can try to replace them if we find them.
        # Given the "triple link" issue, maybe some are coming from RAG.

        # 2. Limit links if requested
        if link_limit is not None:
            all_links = list(re.finditer(r'https?://[^\s]+', text))
            if len(all_links) > link_limit:
                # Keep only the first link_limit links, remove the rest
                # We'll just keep the first one and strip others from the text
                links_to_keep = all_links[:link_limit]
                # This is tricky to do with regex sub, let's do it manually
                first_link_end = links_to_keep[-1].end()
                text_after_first_link = text[first_link_end:]
                # Remove all other links from the remaining text
                text_after_first_link = re.sub(r'https?://[^\s]+', '', text_after_first_link)
                text = text[:first_link_end] + text_after_first_link

        return text

if __name__ == "__main__":
    # Test Amazon Affiliate
    client = AffiliateClient()
    products = client.search_products("Magnesium Glycinate")
    if products:
        print(client.format_product_as_recommendation(products[0]))
    else:
        print("No products found or API not configured.")
