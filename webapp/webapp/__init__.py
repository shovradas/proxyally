"""
The flask application package.
"""

import os
from flask import Flask
from config import API_ROOT

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32) # CSRF secret key
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["API_ROOT"] = API_ROOT

import webapp.filters
import webapp.views
