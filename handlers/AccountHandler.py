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

from handlers.Helpers import *
from handlers.User import User
from MainHandler import Handler

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class AccountHandler(db.Model):
	def get(self):
		#On récupère l'utilisateur connecté
		user = None

		cookie = self.request.cookies.get('user_id')
		if cookie:
			secure_val = check_secure_val(cookie)
			if secure_val:
				id = int(secure_val)
				user = User.get_by_id(id)

		self.render("account.html", user)