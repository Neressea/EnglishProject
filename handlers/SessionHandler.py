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

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Login(Handler):
	def render_page(self, username="", password="", error=""):
		self.render("front.html", username=username, password=password, error=error)

	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")

		if username and password:
			verif_user = db.GqlQuery("SELECT * FROM User WHERE username = :1", username)
			user = verif_user.get()
			if user is None:
				error="There is an error in the login"
				self.render_page(username, password, error)
			else:
				if valid_pw(user.username, password, user.password):
					string_id = str(user.key().id())
					secure_val = make_secure_val(string_id)
					self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % secure_val)
					self.redirect('/')
				else:
					error="There is an error in the login"
					self.render_page(username, password, error)
		else:
			error = "One field is empty"
			self.render_page(username, password, error)

class Logout(Handler):
	def get(self):
		cookie = self.request.cookies.get('user_id')
		if cookie:
			self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
		self.redirect("/")