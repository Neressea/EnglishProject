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
import time
import re

from handlers.Helpers import *
from MainHandler import Handler
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

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
	questions_comprehension = db.ListProperty(item_type = db.Text, required = True) #Question directe. Question séparée de la réponse par un "|"

class CreateLesson(Handler):
	def render_page(self, title="", content="", error=""):
		self.render("create_lesson.html")

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

		#On commence par créer la leçon
		lesson = Lesson(difficulty = difficulty, title = title)
		lesson.put()
		id_lesson = lesson.key().id()

		stories = self.request.get_all("story")

		#On parcourt toutes les histoires
		for i in range(0, len(stories)):
			#On récupère les textes à trous en l'état
			holes = self.request.get_all("vocabulary-question"+str(i+1)) # i = numéro de l'histoire
			for j in range(0, len(holes)):
				holes[j] = db.Text(holes[j])

			#On récupère les QCMs
			QCMs = self.request.get_all("grammar-question"+str(i+1))

			#On récupère les réponses de chaque QCM
			for j in range(0, len(QCMs)):
				QCMs_responses = self.request.get_all("grammar-answer"+str(i+1)+str(j+1))
				#On parcourt ces réponses et on combine le tout
				for k in range(0, len(QCMs_responses)):
					QCMs[j] = db.Text(QCMs[j] + "|" + QCMs_responses[k])

			logging.error(QCMs)

			#On récupère les questions directes
			directs = self.request.get_all("comprehension-question"+str(i+1))

			#On récupère les réponses
			directs_responses = self.request.get_all("comprehension-answer"+str(i+1))

			#On combine les deux
			for j in range(0, len(directs)):
				directs[j] = db.Text(directs[j] + "|" + directs_responses[j])

			logging.error(directs)

			#On crée l'objet Story courant
			stry = Story(id_lesson = id_lesson, text=stories[i], questions_vocabulary = holes, questions_grammar = QCMs, questions_comprehension = directs)
			stry.put()

		time.sleep(0.5)

		self.redirect('/'+str(id_lesson))

class LessonPage(Handler):
	def get(self, id):
		key = db.Key.from_path('Lesson', int(id))
		lesson = db.get(key)

		if not lesson:
			self.error(404)
			return

		stories = db.GqlQuery("SELECT * FROM Story WHERE id_lesson = :1", int(id)).fetch(100)

		begin = re.escape("[hole]")
		end = re.escape("[/hole]")
		search = begin + r'.*' + end
		
		for i in range(0, len(stories)):
			for j in range(0, len(stories[i].questions_vocabulary)):
				stories[i].questions_vocabulary[j] = re.sub(search, "<input type=\"text\" id=\"vocabulary-answer{{i}}{{j}}\" name=\"vocabulary-answer{{i}}{{j}}\"/>", stories[i].questions_vocabulary[j])
				logging.error(stories[i].questions_vocabulary[j] )

		self.render("lesson.html", lesson=lesson, stories=stories)