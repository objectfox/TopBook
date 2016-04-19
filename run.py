#!/usr/bin/env python

from topbook import TopBook

from bottle import route, run, request
import json, os, re, sys
from string import lower

# Use gevent if we have it for multiple requests
gevent = False
try:
	from gevent import monkey; monkey.patch_all()
	gevent = True
except:
	pass

accounts = {}

# If our environment variables are set, just use those without a config.
# This is the heroku-style use case.

if len(sys.argv) > 1:
	port = sys.argv[1]
else:
	port = 8000

if os.environ.get('SLACK_TOKEN') and os.environ.get('FB_TOKEN'):
	options = {}
	try:
		with open("config.json", 'r') as jsonfile:
		    cfg = json.loads(jsonfile.read())
		for app in cfg.keys():
			options.update(cfg[app]['pages'])
	except:
		pass

	app = {
		"slacktoken": os.environ['SLACK_TOKEN'],
		"fbtoken": os.environ['FB_TOKEN'],
		"pages": options
	}
	accounts[os.environ['SLACK_TOKEN']] = TopBook(app)
else:
	with open("config.json", 'r') as jsonfile:
	    cfg = json.loads(jsonfile.read())
	for app in cfg.keys():
		accounts[cfg[app]['slacktoken']] = TopBook(cfg[app])


@route("/")
def hello():
	return "Hello World.\n"

@route("/slack", method='POST')
def slack_parse():
	help = [
{"title":"pages","text": "list of configured page options"},
{"title":"likes/comments/shares page/page1, page2, .../page_group",
"text": """
Example: top 3 relative likes for vox, sbnation in the last 2 days
Options:
 (top) X - number of results (default: 1)
 relative - sort results compared to page average (optional)
 likes/comments/shares - metric to sort on
 (for) page/pages1,page2,.../page_group - FB page, list of FB pages, or a config page group
 (in the last) X days - day age range (default: 1)
"""
}
]

	response = {}

	token = request.forms.get('token')
	if accounts[token]:
		topbook = accounts[token]
	else:
		return {"text":"Slack token not found in config."}

	user_name = request.forms.get('user_name')
	trigger_word = request.forms.get('trigger_word')
	text = request.forms.get('text')
	if text.startswith(trigger_word):
		text = text[len(trigger_word):].lstrip()

	count = 1
	m = re.search('^(\d+)\s(.+)$', text)
	m2 = re.search('^top\s+(\d+)\s+(.+)$', text)
	if m and m.group(2):
		count = int(m.group(1))
		text = m.group(2)
	elif m2 and m2.group(2):
		count = int(m2.group(1))
		text = m2.group(2)

	days = 1
	m = re.search('^(.*) (in|for) the last (\d+) days?', text)
	m2 = re.search('^(.*) (in|for) last (\d+) days?', text)
	m3 = re.search('^(.*) last (\d+) days?', text)
	m4 = re.search('^(.*) (\d+) days?', text)
	if m and m.group(2):
		text = m.group(1)
		days = int(m.group(3))
	elif m2 and m2.group(2):
		text = m2.group(1)
		days = int(m2.group(3))
	elif m3 and m3.group(2):
		text = m3.group(1)
		days = int(m3.group(2))
	elif m4 and m4.group(2):
		text = m4.group(1)
		days = int(m4.group(2))

	relative = False
	if lower(text).startswith('relative'):
		text = text[len("relative"):].lstrip()
		relative = True

	if lower(text).startswith('help'):
		response["attachments"] = help
	elif lower(text).startswith('pages'):
		response = topbook.page_list()
	elif lower(text).startswith('likes'):
		response = topbook.lookup('likes', text[5:].lstrip(), days, relative, count)
	elif lower(text).startswith('comments'):
		response = topbook.lookup('comments', text[8:].lstrip(), days, relative, count)
	elif lower(text).startswith('shares'):
		response = topbook.lookup('shares', text[6:].lstrip(), days, relative, count)
	else:
		response['text'] = "Ack! I don't know how to answer that. Try `%s help`?" % trigger_word


	return response

if gevent:
	run(host='0.0.0.0', port=port, debug=True, reloader=True, server='gevent')
else:
	run(host='0.0.0.0', port=port, debug=True, reloader=True)

