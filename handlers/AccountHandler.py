#!/usr/bin/env python
# encoding=utf8  
import sys 
reload(sys)  
sys.setdefaultencoding('utf8')

import os
import re
import sys
import webapp2
import jinja2
import random

from handlers.Helpers import *
from handlers.User import User
from MainHandler import Handler
from LessonHandler import Lesson
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class AccountHandler(Handler):
	def get(self):
		cookie = self.request.cookies.get('user_id')
		user = None
		if cookie:
			secure_val = check_secure_val(cookie)
			if secure_val:
				id = int(secure_val)
				user = User.get_by_id(id)
		lessons = []
		if user:
			lessons_ids = user.lessons_done
			for i in range(0, len(lessons_ids)):
				lesson = Lesson.get_by_id(lessons_ids[i])
				lessons.append(lesson)

		lessons.reverse()

		self.render("account.html", lessons=lessons)

class TrainingHandler(Handler):
	def get(self):
		#On récupère l'utilisateur authentifié
		cookie = self.request.cookies.get('user_id')
		user = None
		if cookie:
			secure_val = check_secure_val(cookie)
			if secure_val:
				user_id = int(secure_val)
				user = User.get_by_id(user_id)

		if user is None:
			self.redirect('/')

		#On regarde là où l'élève a le moins de points
		training = None
		m = min(user.grade_vocabulary, user.grade_grammar, user.grade_comprehension)
		if user.grade_vocabulary == m:
			training = "Vocabulary"
		elif user.grade_grammar == m:
			training = "Grammar"
		else:
			training = "Comprehension"

		#On récupère dans la BD une leçon où la proportion de questions sur ce thème est le plus important et qu'il n'a pas déjà faite
		lessons = None
		try:
			lessons = db.GqlQuery("SELECT * FROM Lesson WHERE dominant = :1", training).fetch(100)
		except db.BadQueryError:
			lessons = None

		lesson = None

		if lessons is not None:
			i = 0
			while i < len(lessons) and lesson is None:
				if lessons[i].key().id() not in user.lessons_done:
					lesson = lessons[i]
				i = i + 1
		stories = []
		if lesson is None:
			training = "FAIL"	
			lessons = db.GqlQuery("SELECT * FROM Lesson ").fetch(100)

		if lessons is None or len(lessons) == 0:
			training = "NO_ONE"
		else:
			lesson = None
						
			while i < len(lessons) and lesson is None:
				if lessons[i].key().id() not in user.lessons_done:
					lesson = lessons[i]
				i = i + 1

			if lesson is None:
				training = "NO_ONE"
			else:
			
				#On récupère toutes les histoires liées à la leçon
				stories = db.GqlQuery("SELECT * FROM Story WHERE id_lesson = :1", lesson.key().id()).fetch(100)

				begin = re.escape("[hole]")
				end = re.escape("[/hole]")
				search = begin + '.*?' + end

				for i in range(0, len(stories)):
					if stories[i].type_of_story == "video":
						stories[i].text = re.sub(re.escape("watch?v="), "embed/", stories[i].text) 

					for j in range(0, len(stories[i].questions_vocabulary)):
						stories[i].questions_vocabulary[j] = re.sub(search, "<input type=\"text\" id=\"vocabulary-answer%d%d\" name=\"vocabulary-answer%d%d\" class=\"voca_hole form-control\"/>" % (i+1, j+1, i+1, j+1), stories[i].questions_vocabulary[j])

		#On renvoie le template avec la leçon et le thème proposé 
		self.render("lesson.html", lesson=lesson, stories=stories, training=training)