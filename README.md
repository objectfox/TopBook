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
topbook list
```

You can for page metrics with like, which returns the most liked article on the Vox Facebook page in the last 24 hours.

```
topbook likes vox
```

You can also create collections, say for all the local news sites in your area, or the sites that follow a specific niche, and ask all of them in one go.

```
topbook comments austinnews
```

# Configuration & Installation

TopBook requires two configuration tokens and a list of pages to monitor. First, you need a Slack Token from your team's Slack Integrations page. Second, you need a Facebook API Token, which you get by creating a new Facebook App and then requesting it in the [Graph API Explorer](https://developers.facebook.com/tools/explorer/). Then, optionally, add some pages and page collections to your file. The syntax is `"nickname": "facebook_page_name"`, or `"nickname": ["List","of","Facebook","page","names"]`. Name this file config.json, and drop it in the same directory as run.py.

Install the dependencies listed in the requirements.txt file, possibly in a [python virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

Start the bottle server with `./run.py`. This will by default create a server on port 8000 on your machine. Then you need to figure out a way to get requests from Slack to that port, or just use the included `slack-test.py` client to post requests to bottle and verify the output.

