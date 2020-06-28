"""
The flask application package.
"""

import os
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32) # CSRF secret key
app.config["TEMPLATES_AUTO_RELOAD"] = True

import webapp.filters
import webapp.views
