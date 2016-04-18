#!/usr/bin/env python

#from topbook import TopBook
import facebook
from string import lower
from datetime import datetime
import urllib2

class NoPostsError(Exception):
	def __init__(self, value=""):
		self.value = value
	def __str__(self):
		return repr(self.value)

class TopBook(object):
	def __init__(self, cfg):
		self.token = cfg['fbtoken']
		self.pages = cfg['pages']
		self.lower_pages = map(lambda w: w.lower(), self.pages)
		self.graph = facebook.GraphAPI(self.token)

	def page_list(self):
		return "Configured pages are: " + ", ".join(self.pages.keys())

	def lookup(self, metric, query, days):
		attachments = []
		page = query
		if lower(query) in self.lower_pages:
			for config_page in self.pages:
				if lower(query) == lower(config_page):
					page = self.pages[config_page]

		# print 'Looking up `%s`.' % query
		top = {}
		if isinstance(page, basestring):
			try:
				top['id'], top['message'], top['likes'], top['comments'], top['picture'], top['shares'] = self.top_for_page(metric, page, days)
			except facebook.GraphAPIError:
				return "Error requesting post list for %s, page may not exist." % page
			except NoPostsError:
				return "No posts on %s in last day." % page
			top['page'] = ''
		elif isinstance(page, (list, tuple)):
			for subpage in page:
				print "Reqesting %s" % subpage
				try:
					post = {}
					post['id'], post['message'], post['likes'], post['comments'], post['picture'], post['shares'] = self.top_for_page(metric, subpage, days)
				except NoPostsError:
					# No posts in time range.
					print "No posts in time range."
					pass
				except Exception, e:
					return "Error requesting post list for %s: %s" % (subpage, e)
				if metric not in top or top[metric] < post[metric]:
					top['page'] = "%s" % subpage
					top['id'] = post['id']
					top['comments'] = post['comments']
					top['likes'] = post['likes']
					top['message'] = post['message']
					top['picture'] = post['picture']
					top['shares'] = post['shares']
		else:
			return "Page not found. Try the pages command for a list."

		message = {
			"fallback": "Fallback",
			"text": "%s http://www.facebook.com/%s" % (top['message'], top['id']),
			"fields": [
                {
                    "title": "Social",
                    "value": "%s Likes, %s Comments, %s Shares" % (top['likes'], top['comments'], top['shares']),
                    "short": True
                }
            ],
			"thumb_url": "%s" % top['picture']
		}
		if top['page']:
			message["fields"].append({"title":"Page","value":top['page'], "short": True})
		attachments.append(message)
		return {"attachments":attachments}
		# return "%s%s with %s likes and %s comments (http://www.facebook.com/%s) (%s)" % (top['page'], top['message'], top['likes'], top['comments'], top['id'], top['picture'])

	def top_for_page(self, metric, page, days):
		profile = self.graph.get_object(page)
		posts = self.graph.get_connections(profile['id'], 'posts?fields=id,message,created_time,picture,comments.limit(1).summary(true),likes.limit(1).summary(true),shares')
		top = {}
		data = []
		completed = False
		while True:
			for post in posts['data']:
				# "2016-04-13T18:04:04+0000"
				created_time = datetime.strptime(post['created_time'],"%Y-%m-%dT%H:%M:%S+0000")
				age = datetime.utcnow() - created_time
				if age.days >= days:
					completed = True
					break
				data.append(post)
			if completed:
				break
			req = urllib2.Request(posts['paging']['next'])
			response = urllib2.urlopen(req)
			posts = json.loads(response.read())
			# posts = requests.get(posts['paging']['next']).json()

		for post in data:
			if metric == "shares":
				if post.get(metric):
					total = post[metric].get('count')
				else:
					total = 0
			else:
				if post.get(metric):
					total = post[metric]['summary']['total_count']
				else:
					total = 0
			if metric not in top or top[metric] < total:
				top['id'] = post['id']
				top['comments'] = post['comments']['summary']['total_count']
				top['likes'] = post['likes']['summary']['total_count']
				top['message'] = post['message']
				top['picture'] = post['picture']
				top['shares'] = post.get('shares',{}).get("count",0)
			# print "%s: %s %s %s" % (page, post['comments']['summary']['total_count'], post['likes']['summary']['total_count'], post['message'])
		if not top:
			raise NoPostsError()
		return (top['id'], top['message'], top['likes'], top['comments'], top['picture'], top['shares'])

# --- Move all this junk to topbook.py when done ---

from bottle import route, run, request
import json
from string import lower
import re

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
likes <account> (last X days) - Show the most liked article for an account
comments <account> (last X days) - Show the most commented article for an account
	"""

	response = {}

	token = request.forms.get('token')
	if accounts[token]:
		topbook = accounts[token]
	else:
		return (json.dumps({"text":"Slack token not found in config."}))

	days = 1

	user_name = request.forms.get('user_name')
	trigger_word = request.forms.get('trigger_word')
	text = request.forms.get('text')
	if text.startswith(trigger_word):
		text = text[len(trigger_word):].lstrip()

	m = re.search('^(.*) in last (\d+) days?', text)
	m2 = re.search('^(.*) last (\d+) days?', text)
	if m and m.group(2):
		text = m.group(1)
		days = int(m.group(2))
	elif m2 and m2.group(2):
		text = m2.group(1)
		days = int(m2.group(2))

	if lower(text).startswith('help'):
		response['text'] = help
	elif lower(text).startswith('pages'):
		response['text'] = topbook.page_list()
	elif lower(text).startswith('likes'):
		response = topbook.lookup('likes', text[5:].lstrip(), days)
	elif lower(text).startswith('comments'):
		response = topbook.lookup('comments', text[8:].lstrip(), days)
	elif lower(text).startswith('shares'):
		response = topbook.lookup('shares', text[6:].lstrip(), days)
	else:
		response['text'] = "Ack! I don't know how to answer that. Try `%s help`?" % trigger_word


	return response


run(host='127.0.0.1', port=8000, debug=True, reloader=True)

