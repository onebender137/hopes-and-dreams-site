# Facebook API Setup Guide for "Hopes and Dreams" Bot

Setting up the Facebook Graph API for your Business Page.

> **Note on Facebook Groups:** As of April 22, 2024, Meta has deprecated the Groups API for third-party apps. This bot focuses on managing and interacting with your **Business Page** only.

## 1. Create a Facebook Developer App
1. Go to [Facebook Developers](https://developers.facebook.com/) and log in.
2. Click **"My Apps"** -> **"Create App."**
3. Select an app type (e.g., "Business") and follow the prompts.

## 2. Get Your Page ID
- **Page ID:** Go to your Facebook Page -> About -> Page Transparency -> Page ID (at the bottom).
  - Your Page ID: `61581034972328`

## 3. Obtain Page Access Token
1. In your App Dashboard, go to **Tools** -> **Graph API Explorer.**
2. In the **"User or Page"** dropdown, select your **Facebook Page.**
3. Add the following **Permissions:**
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
4. Click **"Generate Access Token."**
5. **Extend the Token:** Use the [Access Token Tool](https://developers.facebook.com/tools/accesstoken/) to debug and "Extend Access Token" to get a long-lived (60-day) token, or generate a permanent one via System Users if you have a Business Manager.

## 4. Update Your `.env` File
Copy the token and ID into your `.env` file:
```bash
FB_PAGE_ID=61581034972328
FB_PAGE_ACCESS_TOKEN=your_copied_page_token
```

## 5. Testing the Connection
Run the client script to verify:
```bash
python fb_client.py
```
If configured correctly, it should print "Facebook Page Client Initialized Successfully."
