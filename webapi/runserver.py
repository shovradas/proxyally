"""
This script runs the webapi application using a development server.
"""

from os import environ
from webapi import app
from config import DEBUG


if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5001'))
    except ValueError:
        PORT = 5001
    app.run(HOST, PORT, debug=DEBUG)    
