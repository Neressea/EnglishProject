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

from google.appengine.ext import db

class User(db.Model):
	isAdmin = db.BooleanProperty(required=True)
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	grade_vocabulary = db.IntegerProperty(default = 0)
	grade_grammar = db.IntegerProperty(default = 0)
	grade_comprehension = db.IntegerProperty(default = 0)
	lessons_done = db.ListProperty(item_type = int) #Liste des IDs des leçons terminées