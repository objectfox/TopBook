#!/usr/bin/env python

#from topbook import TopBook
import facebook
from string import lower, replace
from datetime import datetime
import urllib2
import locale

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
		if not self.pages:
			return {"text": "There aren't any pages configured."}
		pages = []
		page_groups = []
		text = []
		for page in self.pages.keys():
			if isinstance(self.pages[page], basestring):
				pages.append(page)
			else:
				page_groups.append(page + " (" + ", ".join(self.pages[page]) + ")" )
		if len(pages) > 0:
			text.append("Configured pages: " + ", ".join(pages))
		if len(page_groups) > 0:
			text.append("Configured page groups: " + ", ".join(page_groups))
		return {"text": "\n".join(text)}

	def lookup(self, metric, query, days, relative, count):
		attachments = []
		if query.startswith("for"):
			query = query[len("for"):].lstrip()
		if query.startswith("from"):
			query = query[len("from"):].lstrip()
		if query.startswith("on"):
			query = query[len("on"):].lstrip()
		page = query
		sortmetric = metric
		all_posts = []
		if relative:
			sortmetric = "perfper"
		page = replace(page, ", ",",")
		if "," in page:
			page = page.split(",")
		elif lower(query) in self.lower_pages:
			for config_page in self.pages:
				if lower(query) == lower(config_page):
					page = self.pages[config_page]

		# print 'Looking up `%s`.' % query
		top = {}
		if isinstance(page, basestring):
			try:
				all_posts = self.top_for_page(metric, page, days)
			except facebook.GraphAPIError:
				return {"text": "Error requesting post list for %s, page may not exist." % page}
			except NoPostsError:
				return {"text": "No posts on %s in last day." % page}
			top['page'] = ''
		elif isinstance(page, (list, tuple)):
			for subpage in page:
				print "Reqesting %s" % subpage
				try:
					all_posts.extend(self.top_for_page(metric, subpage, days))
				except NoPostsError:
					# No posts in time range.
					print "No posts in time range."
					pass
				except Exception, e:
					return {"text": "Error requesting post list for %s: %s" % (subpage, e)}
			all_posts.sort(key=lambda x: x.get(sortmetric), reverse=True)
		else:
			return {"text": "Page not found. Try the pages command for a list."}

                    # "value": "%s :thumbsup:, %s :speech_balloon:, %s :arrow_heading_up:" % (
		for x in range(count):
			top = all_posts[x]
			message = {
				"fallback": "Fallback",
				"text": "%s http://www.facebook.com/%s" % (top['message'], top['id']),
				"fields": [
	                {
	                    "title": "Social",
	                    "value": "%s Likes, %s Comments, %s Shares" % (
	                    		locale.format("%d", top['likes'], grouping=True),
	                    		locale.format("%d", top['comments'], grouping=True),
	                    		locale.format("%d", top['shares'], grouping=True)),
	                    "short": True
	                },
	                {
	                    "title": "Performance",
	                    "value": "%%%s of page average (%s)" % (
	                    		locale.format("%d", top['perfper'], grouping=True),
	                    		locale.format("%d", top['average'], grouping=True)),
	                    "short": True
	                }

	            ],
				"thumb_url": "%s" % top['picture']
			}
			if isinstance(page, (list, tuple)):
				message["fields"].append({"title":"Page","value":"<http://www.facebook.com/%s|%s>" % (top['page'], top['page']), "short": True})
			attachments.append(message)
		return {"attachments":attachments}
		# return "%s%s with %s likes and %s comments (http://www.facebook.com/%s) (%s)" % (top['page'], top['message'], top['likes'], top['comments'], top['id'], top['picture'])

	def top_for_page(self, metric, page, days):
		profile = self.graph.get_object(page)
		posts = self.graph.get_connections(profile['id'], 'posts?fields=id,message,created_time,picture,comments.limit(1).summary(true),likes.limit(1).summary(true),shares')
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
		totals = []
		posts = []
		top = {}
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
			totals.append(total)
			top = {}
			top['id'] = post['id']
			top['page'] = page
			top['comments'] = post['comments']['summary']['total_count']
			top['likes'] = post['likes']['summary']['total_count']
			top['message'] = post.get('message',"")
			top['picture'] = post.get('picture',"")
			top['shares'] = post.get('shares',{}).get("count",0)
			top['average'] = 0
			top['perfper'] = 100.0
			posts.append(top)
			# print "%s: %s %s %s" % (page, post['comments']['summary']['total_count'], post['likes']['summary']['total_count'], post['message'])
		if not top:
			raise NoPostsError()
		average = 0
		perfper = 100.0
		if totals:
			average = sum(totals)/len(totals)
			if average > 0:
				perfper = (float(top[metric])/float(average))*100.0
		postlist = []
		for post in posts:
			post["average"] = average
			if average > 0:
				post["perfper"] = (float(post[metric])/float(average))*100.0
			else:
				post["perfper"] = 100.0
			postlist.append(post)

		return sorted(postlist, key=lambda x: x.get(metric), reverse=True)

# --- Move all this junk to topbook.py when done ---

from bottle import route, run, request
import json, os, re, sys
from string import lower

accounts = {}

# If our environment variables are set, just use those without a config.
# This is the heroku-style use case.

if len(sys.argv) > 1:
	port = sys.argv[1]
else:
	port = 8000

if os.environ.get('SLACK_TOKEN') and os.environ.get('FB_TOKEN'):
	app = {
		"slacktoken": os.environ['SLACK_TOKEN'],
		"fbtoken": os.environ['FB_TOKEN'],
		"pages": {}
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
	locale.setlocale(locale.LC_ALL, 'en_US')

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


run(host='0.0.0.0', port=port, debug=True, reloader=True)

