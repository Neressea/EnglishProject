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
from handlers.UserHandler import User
from xml.dom import minidom

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

#Une leçon est liée à des histoires par la base de données (id)
class Lesson(db.Model):
	difficulty = db.StringProperty(required = True, choices=set(["Easy", "Medium", "Hard"]))
	title = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)
	dominant = db.StringProperty(choices=set(["Vocabulary", "Grammar", "Comprehension", "Balanced"]))

class Story(db.Model):
	id_lesson = db.IntegerProperty(required = True)
	num_story = db.IntegerProperty(required = True)
	title = db.StringProperty(required = True)
	type_of_story = db.StringProperty(required = True)
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

		stories = self.request.get_all("story_text")

		nb_questions = [0, 0, 0]

		#On parcourt toutes les histoires
		for i in range(0, len(stories)):
			title_story = self.request.get("title_story"+str(i+1))
			type_of_story = self.request.get("type_of_story"+str(i+1))

			#On récupère les textes à trous en l'état
			holes = self.request.get_all("vocabulary-question"+str(i+1)) # i = numéro de l'histoire
			for j in range(0, len(holes)):
				nb_questions[0] += 1
				holes[j] = db.Text(holes[j])

			#On récupère les QCMs
			QCMs = self.request.get_all("grammar-question"+str(i+1))

			#On récupère les réponses de chaque QCM
			for j in range(0, len(QCMs)):
				nb_questions[1] += 1
				QCMs_responses = self.request.get_all("grammar-answer"+str(i+1)+str(j+1))
				#On parcourt ces réponses et on combine le tout
				for k in range(0, len(QCMs_responses)):
					QCMs[j] = db.Text(QCMs[j] + "|" + QCMs_responses[k])

			#On récupère les questions directes
			directs = self.request.get_all("comprehension-question"+str(i+1))

			#On récupère les réponses
			directs_responses = self.request.get_all("comprehension-answer"+str(i+1))

			#On combine les deux
			for j in range(0, len(directs)):
				nb_questions[2] += 1
				directs[j] = db.Text(directs[j] + "|" + directs_responses[j])

			#On crée l'objet Story courant
			stry = Story(type_of_story = type_of_story, title=title_story, id_lesson = id_lesson, text=stories[i], questions_vocabulary = holes, questions_grammar = QCMs, questions_comprehension = directs, num_story = i)
			stry.put()

		#On MàJ la dominante de la leçon
		if nb_questions[0] > nb_questions[1] and nb_questions[0]>nb_questions[2]:
			lesson.dominant = "Vocabulary"
		elif nb_questions[1] > nb_questions[0] and nb_questions[1]>nb_questions[2]:
			lesson.dominant = "Grammar"
		elif nb_questions[2] > nb_questions[0] and nb_questions[2]>nb_questions[1]:
			lesson.dominant = "Comprehension"
		else:
			lesson.dominant = "Balanced" #C'est équilibré.

		lesson.put()

		time.sleep(0.5)

		self.redirect('/'+str(id_lesson))

class CheckHandler(Handler):
	def post(self):
		cookie = self.request.cookies.get('user_id')
		if not cookie:
			self.redirect('/')

		#On récupère l'utilisateur authentifié
		user_id = int(cookie.split("|")[0])
		user = User.get_by_id(user_id)

		#we get the id oh the lesson
		lesson_id = self.request.get('id-lesson')

		#On récupère la leçon
		lesson = Lesson.get_by_id(int(lesson_id))

		#we get all the relative stories
		stories_correction = db.GqlQuery("SELECT * FROM Story WHERE id_lesson = :1", int(lesson_id)).fetch(100)

		#réponses correctes
		holes = []
		QCMs = []
		comprehensions = []

		#réponses reçues
		vcbl_ans=[]
		gramm_ans=[]
		cpr_ans=[]

		#List representing the answers. 1 if the answer was ok, else 0.
		vocabulary_results = []
		grammar_results = []
		comprehension_results = []

		#Tableau 2D. Contient toutes les corrections de vocabulaire à afficher.
		vocabulary_parts = []

		#On parcourt toutes les histoires
		for i in range(0, len(stories_correction)):

			#On récupère les textes à trous en l'état
			holes = stories_correction[i].questions_vocabulary

			for j in range(0, len(holes)):
				#On compare chaque réponse au résultat attendu
				vocable_fields = self.request.get_all("vocabulary-answer%d%d" % (i+1, j+1))
				begin = re.escape("[hole]")
				end = re.escape("[/hole]")
				search = begin + '.*?' + end
				to_find = re.findall(search, holes[j])
				
				#On split et on enlève les trous
				sentences = re.split(search, holes[j])
				vocabulary_parts.append("")

				for k in range(0, len(vocable_fields)):
					vocabulary_parts[i+j] += sentences[k]
					vcbl_ans.append(vocable_fields[k])
					to_find[k] = to_find[k].replace('[hole]', '')
					to_find[k] = to_find[k].replace('[/hole]', '')

					logging.error(vcbl_ans[len(vcbl_ans)-1])

					if to_find[k] == vcbl_ans[len(vcbl_ans)-1]:
						vocabulary_results.append(1)
						vocabulary_parts[i+j]+="<input class=\"answer_true\" type=\"text\" name=\"pseudo\" value=\""+vcbl_ans[len(vcbl_ans)-1]+"\" disabled=\"disabled\" />"
					else:
						vocabulary_results.append(0)
						vocabulary_parts[i+j]+="<input class=\"answer_false voca_hole form-control\" type=\"text\" name=\"pseudo\" value=\""+vcbl_ans[len(vcbl_ans)-1]+"\" disabled=\"disabled\" />"
						vocabulary_parts[i+j]+="<input class=\"answer_true voca_hole form-control\" type=\"text\" name=\"pseudo\" value=\""+to_find[k]+"\" disabled=\"disabled\" />"

			#On parcourt toutes les QCMs
			QCMs = stories_correction[i].questions_grammar
			for j in range(0, len(QCMs)):
				#On récupère la réponse à la question courante
				gramm_ans.append(self.request.get("grammar-answer%d%d" % (i+1, j+1)))
				grammar_results.append(1 if QCMs[j].split("|")[1] == gramm_ans[i+j] else 0)

			#On parcourt toutes les questions directes
			comprehensions = stories_correction[i].questions_comprehension
			for j in range(0, len(comprehensions)):
				#On récupère la réponse à la question courante
				cpr_ans.append(self.request.get("comprehension-answer%d%d" % (i+1, j+1)))
				comprehension_results.append(1 if comprehensions[j].split("|")[1] == cpr_ans[i+j] else 0)

			if stories_correction[i].type_of_story == "video":
				stories_correction[i].text = re.sub(re.escape("watch?v="), "embed/", stories_correction[i].text) 

		percentages = [0, 0, 0]
		percentages[0] = int(((sum(vocabulary_results) +0.0) / len(vocabulary_results))) * 100 if len(vocabulary_results) > 0 else 0
		percentages[1] = int((sum(grammar_results) +0.0) / len(grammar_results) * 100)
		percentages[2] = int((sum(comprehension_results) +0.0) / len(comprehension_results) * 100)

		#On met à jour les notes
		user.grade_vocabulary = int((user.grade_vocabulary * len(user.lessons_done) + percentages[0]) / (len(user.lessons_done) + 1))
		user.grade_grammar = int((user.grade_grammar * len(user.lessons_done) + percentages[1]) / (len(user.lessons_done) + 1)) 
		user.grade_comprehension = int((user.grade_comprehension * len(user.lessons_done) + percentages[2]) / (len(user.lessons_done) + 1)) 

		#On met à jour l'utilisateur que si la leçon n'existe pas déjà
		if int(lesson_id) not in user.lessons_done:
			user.lessons_done.append(int(lesson_id))

		user.put()

		#On redirige sur la page de résultats
		self.render("results.html", lesson=lesson, stories=stories_correction, percentages=percentages, vocabulary_answers=holes, vocabulary_parts = vocabulary_parts,
			grammar_answers=QCMs, comprehension_answers=comprehensions, grammar_got=gramm_ans, comprehension_got=cpr_ans)

class LessonPage(Handler):
	def get(self, id):
		key = db.Key.from_path('Lesson', int(id))
		lesson = db.get(key)

		if not lesson:
			self.redirect('/')
			return

		stories = db.GqlQuery("SELECT * FROM Story WHERE id_lesson = :1 ORDER BY num_story", int(id)).fetch(100)

		begin = re.escape("[hole]")
		end = re.escape("[/hole]")
		search = begin + '.*?' + end

		for i in range(0, len(stories)):
			if stories[i].type_of_story == "video":
				stories[i].text = re.sub(re.escape("watch?v="), "embed/", stories[i].text) 

			for j in range(0, len(stories[i].questions_vocabulary)):
				stories[i].questions_vocabulary[j] = re.sub(search, "<input type=\"text\" id=\"vocabulary-answer%d%d\" name=\"vocabulary-answer%d%d\" class=\"form-control voca_hole\"/>" % (i+1, j+1, i+1, j+1), stories[i].questions_vocabulary[j])

		self.render("lesson.html", lesson=lesson, stories=stories)