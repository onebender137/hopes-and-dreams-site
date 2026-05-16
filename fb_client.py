import os
import random
import facebook
from config import Config

class FBClient:
    def _apply_unicode_style(self, text: str):
        """Converts ALL CAPS lines into Mathematical Bold Unicode characters for high-impact FB headers."""
        if not text:
            return text

        def to_bold(line):
            # Skip if it looks like a URL or is too short to be a header
            if "http" in line or len(line.strip()) < 3:
                return line

            out = ""
            for char in line:
                codepoint = ord(char)
                if 65 <= codepoint <= 90: # A-Z
                    out += chr(codepoint + 119743)
                elif 97 <= codepoint <= 122: # a-z
                    out += chr(codepoint + 119737)
                elif 48 <= codepoint <= 57: # 0-9
                    out += chr(codepoint + 120744)
                else:
                    out += char
            return out

        # Match lines that are purely uppercase (allowing for numbers and spaces/punctuation)
        # We only style lines that are at least 3 chars long and primarily uppercase.
        lines = text.split('\n')
        styled_lines = []
        for line in lines:
            stripped = line.strip()
            # If line is ALL CAPS and significant, bold it.
            if stripped.isupper() and len(stripped) >= 3:
                styled_lines.append(to_bold(line))
            else:
                styled_lines.append(line)

        return '\n'.join(styled_lines)

    def __init__(self, page_access_token=None):
        """Initializes the Facebook Graph API client for Page management."""
        self.page_token = page_access_token or Config.FB_PAGE_ACCESS_TOKEN
        self.page_graph = facebook.GraphAPI(self.page_token) if self.page_token else None
        self.page_id = Config.FB_PAGE_ID
        self.base_media_path = "media"

    def get_smart_image(self, message_content: str):
        """
        Analyzes the post text and selects a random image from the matching subfolder.
        Folders should be: media/nicotine, media/astral, media/kratom, media/general
        """
        topic_map = {
            "nicotine": ["nicotine", "patch", "asprey", "acetylcholine"],
            "astral": ["astral", "dream", "vibration", "sleep paralysis", "separation"],
            "kratom": ["kratom", "alkaloid", "mitragynine", "7-oh"],
        }

        selected_folder = "general"
        content_lower = message_content.lower()

        # Check for keywords in the post content to pick the folder
        for folder, keywords in topic_map.items():
            if any(kw in content_lower for kw in keywords):
                selected_folder = folder
                break

        target_dir = os.path.join(self.base_media_path, selected_folder)

        # Fallback if folder doesn't exist
        if not os.path.exists(target_dir):
            print(f"Warning: Folder {target_dir} not found. Using media root.")
            target_dir = self.base_media_path

        try:
            images = [f for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if images:
                return os.path.join(target_dir, random.choice(images))
        except Exception as e:
            print(f"Error selecting image: {e}")
        
        return None

    def post_to_page(self, message: str, image_path: str = None):
        """Posts to Facebook Page. If image_path is None, it tries to pick one automatically."""
        if not self.page_graph:
            print("Error: Page Graph API client not initialized.")
            return None

        # Apply Syndicate Unicode styling to headers
        message = self._apply_unicode_style(message)

        # If no specific image was passed, use the smart selector
        final_image = image_path or self.get_smart_image(message)

        if final_image and os.path.exists(final_image):
            try:
                with open(final_image, 'rb') as img:
                    print(f"Syndicate posting with image: {final_image}")
                    return self.page_graph.put_photo(image=img, message=message)
            except Exception as e:
                # CRITICAL: put_photo can raise AFTER the post succeeded server-side
                # (timeout, malformed response, network blip). Falling back to text-only
                # creates a duplicate post on FB. Abort instead — operator can retry manually.
                print(f"Error posting photo to Page: {e}")
                print("ABORTING to prevent duplicate post. Check FB manually — image post may have actually succeeded.")
                return None

        # Text-only fallback (only reached when no image was attempted)
        try:
            return self.page_graph.put_object(self.page_id, "feed", message=message)
        except facebook.GraphAPIError as e:
            print(f"Error posting to Page: {e}")
            return None

    def get_recent_posts(self, target_id=None):
        """Fetches recent posts from the Page feed."""
        if not self.page_graph:
            print("Error: Page Graph API client not initialized.")
            return []
        target = target_id or self.page_id
        try:
            posts = self.page_graph.get_connections(target, "posts")
            return posts.get('data', [])
        except facebook.GraphAPIError as e:
            print(f"Error fetching posts from {target}: {e}")
            return []

    def get_comments(self, post_id: str):
        """Fetches comments for a specific post on the Page."""
        if not self.page_graph:
            print("Error: Page Graph API client not initialized.")
            return []
        try:
            comments = self.page_graph.get_connections(post_id, "comments")
            return comments.get('data', [])
        except facebook.GraphAPIError as e:
            print(f"Error fetching comments for post {post_id}: {e}")
            return []

    def reply_to_comment(self, comment_id: str, message: str):
        """Replies to a specific comment using the Page token."""
        if not self.page_graph:
            print("Error: Page Graph API client not initialized.")
            return None
        try:
            return self.page_graph.put_object(comment_id, "comments", message=message)
        except facebook.GraphAPIError as e:
            print(f"Error replying to comment {comment_id}: {e}")
            return None

if __name__ == "__main__":
    if Config.validate():
        client = FBClient()
        print("Facebook Page Client Initialized Successfully with Smart Media Logic.")
    else:
        print("Facebook Client could not be initialized due to missing configuration.")