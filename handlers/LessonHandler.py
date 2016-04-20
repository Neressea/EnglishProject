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

from handlers.Helpers import *
from MainHandler import Handler
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


def front_lessons(update = False):
	lessons = Lesson.all().order("-created")
	lessons = list(lessons)
	return lessons

#Une leçon est liée à des histoires par la base de données (id)
class Lesson(db.Model):
	difficulty = db.StringProperty(required = True, choices=set(["Easy", "Medium", "Hard"]))
	title = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)

class Story(db.Model):
	id_lesson = db.IntegerProperty(required = True)
	text = db.TextProperty(required = True)
	questions_vocabulary = db.ListProperty(item_type = db.Text, required = True) #Texte à trous. "Mots troués" -> indiqués entre "<hole></hole>"
	questions_grammar = db.ListProperty(item_type = db.Text, required = True) #QCM. Champs séparés par des "|". Premier champ -> question, second -> bonne réponse, et les autres : mauvaises réponses
	questions_compehension = db.ListProperty(item_type = db.Text, required = True) #Question directe. Question séparée de la réponse par un "|"

class CreateLesson(Handler):
	def render_page(self, title="", content="", error=""):
		self.render("create_lesson.html", title=title, content=content, error=error)

	def get(self):
		cookie = self.request.cookies.get('user_id')
		auth = True
		if cookie:
			secure_val = check_secure_val(cookie)
			if secure_val is None:
				auth = False
		else:
			auth = False
				
		self.render("create_lesson.html", auth=auth)

	def post(self):
		cookie = self.request.cookies.get('user_id')
		if not cookie:
			self.redirect('/')

		title = self.request.get("title")
		difficulty = self.request.get("difficulty")

		if title and difficulty:
			stry = Lesson(title=title, difficulty=difficulty)
			stry.put()
			age_set(str(stry.key().id), stry)
			front_lessons(True)
			self.redirect('/blog/'+str(stry.key().id()))
		else:
			error = "We need both title and a content !"
			self.render_page(title, content, error)

class LessonPage(Handler):
	def get(self, id):
		key = db.Key.from_path('Lesson', int(id))
		lesson = db.get(key)

		if not lesson:
			self.error(404)
			return

		self.render("lesson.html", lesson=lesson)