#!/usr/bin/env python

#from topbook import TopBook
import facebook
from string import lower
from datetime import datetime
import requests

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
				print 'Looking up `%s`.' % query
				top = {}
				if isinstance(self.pages[page], basestring):
					# try:
					top['id'], top['message'], top['likes'], top['comments'] = self.top_for_page(metric, self.pages[page])
					# except:
					# 	return "Error requesting post list for %s." % self.pages[page]
					top['page'] = ''
				elif isinstance(self.pages[page], (list, tuple)):
					for subpage in self.pages[page]:
						print "Reqesting %s" % subpage
						try:
							post = {}
							post['id'], post['message'], post['likes'], post['comments'] = self.top_for_page(metric, subpage)
						except:
							return "Error requesting post list for %s." % subpage
						if metric not in top or top[metric] < post[metric]:
							top['page'] = "[%s] " % subpage
							top['id'] = post['id']
							top['comments'] = post['comments']
							top['likes'] = post['likes']
							top['message'] = post['message']
				else:
					return "Page not found. Try the pages command for a list."

				return "%s%s with %s likes and %s comments (http://www.facebook.com/%s)" % (top['page'], top['message'], top['likes'], top['comments'], top['id'])
		return "Page not found. Try the pages command for a list."

	def top_for_page(self, metric, page):
		profile = self.graph.get_object(page)
		posts = self.graph.get_connections(profile['id'], 'posts?fields=id,message,created_time,comments.limit(1).summary(true),likes.limit(1).summary(true)')
		top = {}
		data = []
		completed = False
		while True:
			for post in posts['data']:
				# "2016-04-13T18:04:04+0000"
				created_time = datetime.strptime(post['created_time'],"%Y-%m-%dT%H:%M:%S+0000")
				age = datetime.utcnow() - created_time
				if age.days >= 1:
					completed = True
					break
				data.append(post)
			if completed:
				break
			posts = requests.get(posts['paging']['next']).json()

		for post in data:
			if metric not in top or top[metric] < post[metric]['summary']['total_count']:
				top['id'] = post['id']
				top['comments'] = post['comments']['summary']['total_count']
				top['likes'] = post['likes']['summary']['total_count']
				top['message'] = post['message']
			# print "%s: %s %s %s" % (page, post['comments']['summary']['total_count'], post['likes']['summary']['total_count'], post['message'])
		return (top['id'], top['message'], top['likes'], top['comments'])

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

