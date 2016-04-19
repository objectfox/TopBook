# Getting a Non-Expiring Facebook Token

The key credential for any app that accesses the Facebook API is a non-expiring Facebook API token. Getting this token isn't straightforward, and the valid key time you get from Facebook can seem arbitrary. These instructions will hopefully work:

1. Create a Facebook Page, if you don't have access to one already. If you want a Facebook token that doesn't expire, it seems like it needs to be a page access token. The page doesn't need to be anything special (perhaps one of your pets needs one?), and if you already have access to a page, you can use that one.
2. Sign up for the [Facebook developer program](https://developers.facebook.com/), and create an App. Names and settings here don't really matter, just leave the app in test mode. Collect the App ID and App Secret from the App's Dashboard.
3. In the [Graph API explorer](https://developers.facebook.com/tools/explorer/), follow these steps:
..1. In the upper right in the `Application: Graph API Explorer` dropdown, select the App you created.
..2. Right below that, in the `Get Token` dropdown, select Get Page Access Token, then the Page you created/picked in 1.
..3. Click the round blue i next to the generated token and copy the Page ID
..4. Copy the token
4. Generate a long-lived token with `extend-token.py`: `./extent-token.py page_id token app_id app_secret`
5. Copy the resulting token into the [token debugger](https://developers.facebook.com/tools/debug/accesstoken/).
6. Click the `Extend Access Token` button at the bottom of the page.
7. Copy the resulting token back into the debug area and debug again.
8. Resulting token should never expire.
