#!/usr/bin/env python

#from topbook import TopBook
import facebook
from string import lower

class TopBook(object):
	def __init__(self, cfg):
		self.token = cfg['fbtoken']
		self.pages = cfg['pages']
		self.graph = facebook.GraphAPI(self.token)
	def page_list(self):
		return "Configured pages are: " + ", ".join(self.pages.keys())
	def lookup(self, metric, query):
		for page in self.pages:
			if lower(query) == lower(page):
				# return 'Looking up `%s`.' % query
				profile = self.graph.get_object(self.pages[page])
				posts = self.graph.get_connections(profile['id'], 'posts?fields=id,message,comments.limit(1).summary(true),likes.limit(1).summary(true)')
				top = {}
				for post in posts['data']:
					if metric not in top or top[metric] < post[metric]['summary']['total_count']:
						top['comments'] = post['comments']['summary']['total_count']
						top['likes'] = post['likes']['summary']['total_count']
						top['message'] = post['message']

				return "%s with %s likes and %s comments." % (top['message'], top['likes'], top['comments'])
		return "Page not found. Try the pages command for a list."

# --- Move all this junk to topbook.py when done ---

from bottle import route, run, request
import json
from string import lower

accounts = {}
with open("config.json", 'r') as jsonfile:
    cfg = json.loads(jsonfile.read())
for app in cfg.keys():
	accounts[cfg[app]['slacktoken']] = TopBook(cfg[app])

@route("/")
def hello():
	return "Hello World.\n"

@route("/slack", method='POST')
def slack_parse():
	help = """
pages - Get a list of pages
likes <account> - Show the most liked article for an account
comments <account> - Show the most commented article for an account
	"""

	response = {}

	token = request.forms.get('token')
	if accounts[token]:
		topbook = accounts[token]
	else:
		return (json.dumps({"text":"Slack token not found in config."}))

	user_name = request.forms.get('user_name')
	trigger_word = request.forms.get('trigger_word')
	text = request.forms.get('text')
	if text.startswith(trigger_word):
		text = text[len(trigger_word):].lstrip()

	# print(text)

	if lower(text).startswith('help'):
		response['text'] = help
	elif lower(text).startswith('pages'):
		response['text'] = topbook.page_list()
	elif lower(text).startswith('likes'):
		response['text'] = topbook.lookup('likes', text[5:].lstrip())
	elif lower(text).startswith('comments'):
		response['text'] = topbook.lookup('comments', text[8:].lstrip())
	else:
		response['text'] = "Ack! I don't know how to answer that. Try `%s help`?" % trigger_word


	return json.dumps(response)


run(host='0.0.0.0', port=8000, debug=True, reloader=True)

