#!/usr/bin/env python

import httplib, urllib, sys, os, json, pprint
from urlparse import urlparse

# Set SLACK_TOKEN if you need a custom token for your config.
env_token = os.environ.get('SLACK_TOKEN')

# Set BOT_HOST if the webapp responds on a different port or hostname.
env_host = os.environ.get('BOT_HOST')

# Set BOT_HOST if the webapp responds on a different port or hostname.
env_trigger = os.environ.get('TRIGGER_WORD')

if len(sys.argv) > 2 or len(sys.argv) == 1:
	exit("Usage: slack-test.py \"Message to send to bot\"")

# Here are slack's example outbound webhook post values.
# 
# token=XXXXXXXXXXXXXXXXXX
# team_id=T0001
# team_domain=example
# channel_id=C2147483705
# channel_name=test
# timestamp=1355517523.000005
# user_id=U2147483697
# user_name=Steve
# text=googlebot: What is the air-speed velocity of an unladen swallow?
# trigger_word=googlebot:

token = env_token if env_token else 'XXXXXXXXXXXXXXXXXX'
host = env_host if env_host else 'http://localhost:8000/slack'
trigger_word = env_trigger if env_trigger else 'googlebot: '

url = urlparse(host)

params = urllib.urlencode({'token': token, 'team_id': 'T0001',
	'team_domain': 'example', 'channel_id': 'C2147483705',
	'channel_name': 'test', 'timestamp': '1355517523.000005',
	'user_id': 'U2147483697', 'user_name': 'Steve',
	'text': trigger_word+' '+sys.argv[1], 'trigger_word': trigger_word})
headers = {"Content-type": "application/x-www-form-urlencoded",
	"Accept": "text/plain"}
conn = httplib.HTTPConnection(url[1])
conn.request("POST", url[2], params, headers)
response = conn.getresponse()
data = response.read()
conn.close()
try:
	data = json.loads(data)
	if data.get('text'):
		text = data.get('text').replace("\\n","\n")
		print(text)
	if data.get('attachments'):
		pp = pprint.PrettyPrinter(indent=2)
		pp.pprint(data.get('attachments'))
except:
	print data
	print "Error from server."

