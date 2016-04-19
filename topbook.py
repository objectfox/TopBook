#!/usr/bin/env python

import facebook
from string import lower, replace
from datetime import datetime
import urllib2, json, locale

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
		try:
			locale.setlocale(locale.LC_ALL, 'en_US.utf8')
		except:
			locale.setlocale(locale.LC_ALL, 'en_US')

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
