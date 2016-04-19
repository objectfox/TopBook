#!/usr/bin/env python

import facebook
import sys

if len(sys.argv) < 3:
	quit("Usage: extend-token.py <page_id> <token> <app_id> <app_secret>")

page_id = sys.argv[1]
token = sys.argv[2]
app_id = sys.argv[3]
app_secret = sys.argv[4]

fb = facebook.GraphAPI(token)
newtoken = fb.extend_access_token(app_id, app_secret)['access_token']

args = {
    'fields': 'access_token',
    'access_token': newtoken
	}

print fb.request(page_id, args=args)
