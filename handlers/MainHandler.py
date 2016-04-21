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

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
    	self.response.write(*a, **kw)

    def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

    def render(self, template, **kw):
		kw["sitename"] = appname
		kw["namepage"] = appname
		cookie = self.request.cookies.get('user_id')
		auth = True
		username = None
		if cookie:
			secure_val = check_secure_val(cookie)
			if secure_val is None:
				auth = False
			else:
				id = int(secure_val)
				username = User.get_by_id(id).username
		else:
			auth = False

		if username:
			kw["user"] = username

		self.write(self.render_str(template, **kw))