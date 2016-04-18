# TopBook
A Slack integrated Python app to analyze Facebook pages

TopBook is a simple Python Bottle application which can be called from an [Outgoing Slack Webhook](https://api.slack.com/outgoing-webhooks). It allows you to ask for the most liked or commented posts for a Facebook page or collection of Facebook pages.

# Features

TopBook lets you quickly determine what the most popular content is on a Facebook page or group of Facebook pages. You can get a list of things it knows how to do with:

```
topbook help
```

You can get a list of pages it knows about with:

```
topbook pages
```

You can for page metrics with like, which returns the most liked article on the Vox Facebook page in the last 24 hours.

```
topbook likes vox
```

You can also create collections, say for all the local news sites in your area, or the sites that follow a specific niche, and ask all of them in one go.

```
topbook comments austinnews
```

```
top X likes/comments/shares page/page1, page2, .../page_group in last X days
  (top) X - return the top X results (default: 1)
  relative - rank results as percentage compared to page average (optional)
  likes/comments/shares - how the results are sorted
  (for) page/pages1, page2, .../page_group 
    - specific FB page, manual list of FB pages, or a page group from the config
  (in the last) X days - return results from the last X days (default: 1)
```

Example complex query: _top 3 relative likes for vox, sbnation, eater in the last 2 days_

# Configuration & Installation

TopBook requires two configuration tokens and a list of pages to monitor. First, you need a Slack Token from your team's Slack Integrations page. Second, you need a Facebook API Token, which you get by creating a new Facebook App and then requesting it in the [Graph API Explorer](https://developers.facebook.com/tools/explorer/). Then, optionally, add some pages and page collections to your file. The syntax is `"nickname": "facebook_page_name"`, or `"nickname": ["List","of","Facebook","page","names"]`. Name this file config.json, and drop it in the same directory as run.py.

Install the dependencies listed in the requirements.txt file, possibly in a [python virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

Start the bottle server with `./run.py`. This will by default create a server on port 8000 on your machine. Then you need to figure out a way to get requests from Slack to that port, or just use the included `slack-test.py` client to post requests to bottle and verify the output.

