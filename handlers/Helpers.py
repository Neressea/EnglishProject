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

  #To hash cookiesF
SECRET = 'GFGIUOCKDSP54FSDEFEDSFGGEDGGF4HBFH46TR6YJ264FDDG5'
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

#To hash passwords
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=make_salt()):
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    print(salt)
    return h == make_pw_hash(name, pw, salt)