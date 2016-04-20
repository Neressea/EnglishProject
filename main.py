#!/usr/bin/env python
# encoding=utf8  
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import webapp2

from handlers.Helpers import *
from handlers.MainHandler import * 
from handlers.SessionHandler import * 
from handlers.LessonHandler import * 
from handlers.UserHandler import *

class MainPage(Handler):
	def get(self):
		#Appname définie dans Helpers

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

		self.render("front.html", sitename = appname, namepage = appname, auth = auth, user = username)

app = webapp2.WSGIApplication([('/', MainPage),
	('/newlesson/?', CreateLesson),
	('/(\d+)/?', LessonPage),
	(r'/login/?', Login),
	(r'/signup/?', CreateUser),
	(r'/logout/?', Logout)],
	debug=True)