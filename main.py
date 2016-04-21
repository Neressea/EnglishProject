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
		lessons = Lesson.all().order("-created")
		lessons = list(lessons)
		self.render("front.html", lessons=lessons)

app = webapp2.WSGIApplication([('/', MainPage),
	('/newlesson/?', CreateLesson),
	('/(\d+)/?', LessonPage),
	(r'/login/?', Login),
	(r'/signup/?', CreateUser),
	(r'/logout/?', Logout),
	(r'/check/?', CheckHandler),
	(r'/account/?', AccountHandler)],
	debug=True)