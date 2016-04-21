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

from Helpers import *
from MainHandler import Handler
from google.appengine.ext import db
from handlers.User import User

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class CreateUser(Handler):
	def render_page(self, username_temp="", password="", error=""):
		self.render("create_user.html", username_temp=username_temp, password=password, error=error)

	def get(self):
		self.render("create_user.html")

	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		verify = self.request.get("verify")

		if username and password and verify:

			#On verifie si le pass est identique a la verif
			if password != verify:
				error = "Password and verification are'nt identical"
				self.render_page(username, password, error)
			else:
				#On verifie si l'utilisateur existe deja
				verif_user = db.GqlQuery("SELECT * FROM User WHERE username = :1", username)
				verif_user.run()
				if verif_user.count() != 0:
					error = "Sorry, but this username is already used !"
					self.render_page(username, password, error)
				else:
					hashpass = make_pw_hash(username, password)
					usr = User(isAdmin = False, password = hashpass, username=username)
					usr.put()
					#On ajoute le cookie
					string_id = str(usr.key().id())
					secure_val = make_secure_val(string_id)
					self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % secure_val)
					self.redirect('/')
		else:
			error = "We need both username, a password and a verification of the password."
			self.render_page(username, password, error)