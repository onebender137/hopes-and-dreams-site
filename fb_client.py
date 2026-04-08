import os
import facebook
from config import Config

class FBClient:
    def __init__(self, page_access_token=None):
        """Initializes the Facebook Graph API client for Page management."""
        # Use Page Access Token for Page actions
        self.page_token = page_access_token or Config.FB_PAGE_ACCESS_TOKEN
        self.page_graph = facebook.GraphAPI(self.page_token) if self.page_token else None
        self.page_id = Config.FB_PAGE_ID

    def post_to_page(self, message: str, image_path: str = None):
        """Posts a message to the Facebook Page (with optional image) using Page Access Token."""
        if not self.page_graph:
            print("Error: Page Graph API client not initialized.")
            return None

        # Try to post with photo if path is provided
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, 'rb') as img:
                    return self.page_graph.put_photo(image=img, message=message)
            except Exception as e:
                print(f"Error posting photo to Page: {e}. Falling back to text-only post.")

        # Text-only fallback (or default if no image_path)
        try:
            return self.page_graph.put_object(self.page_id, "feed", message=message)
        except facebook.GraphAPIError as e:
            print(f"Error posting to Page: {e}")
            return None

    def get_recent_posts(self, target_id=None):
        """Fetches recent posts from a Page feed."""
        target_id = target_id or self.page_id
        if not self.page_graph:
            print("Error: Page Graph API client not initialized.")
            return []
        try:
            posts = self.page_graph.get_connections(target_id, "feed")
            return posts.get('data', [])
        except facebook.GraphAPIError as e:
            print(f"Error fetching posts from {target_id}: {e}")
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

    # Note: Group methods (post_to_group, etc.) have been removed as the
    # Facebook Groups API was deprecated by Meta on April 22, 2024.

if __name__ == "__main__":
    if Config.validate():
        client = FBClient()
        print("Facebook Page Client Initialized Successfully.")
    else:
        print("Facebook Client could not be initialized due to missing configuration.")
