#!/usr/bin/env python
# encoding=utf8  
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')

import os
import webapp2
import jinja2
import hmac
import hashlib
import random
import string
import logging

import Helpers
from MainHandler import Handler
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


def front_stories(update = False):
	stories = Story.all().order("-created")
	stories = list(stories)
	return stories

class Story(db.Model):
	content = db.TextProperty(required = True)
	title = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)

class CreateStory(Handler):
	def render_page(self, title="", content="", error=""):
		self.render("create_story.html", title=title, content=content, error=error)

	def get(self):
		cookie = self.request.cookies.get('user_id')
		auth = True
		if cookie:
			secure_val = check_secure_val(cookie)
			if secure_val is None:
				auth = False
		else:
			auth = False
				
		self.render("create_story.html", auth=auth)

	def post(self):
		cookie = self.request.cookies.get('user_id')
		if not cookie:
			self.redirect('/')

		title = self.request.get("title")
		content = self.request.get("content")

		if title and content:
			stry = Story(content = content, title=title)
			stry.put()
			age_set(str(stry.key().id), stry)
			front_stories(True)
			self.redirect('/blog/'+str(stry.key().id()))
		else:
			error = "We need both title and a content !"
			self.render_page(title, content, error)

class StoryPage(Handler):
	def get(self, id):
		key = db.Key.from_path('Story', int(id))
		story = db.get(key)

		if not story:
			self.error(404)
			return

		self.render("story.html", story=story)