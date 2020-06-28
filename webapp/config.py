from os import environ

DEBUG = True
API_ROOT = environ.get('API_ROOT', 'http://localhost:5001/api/v1')