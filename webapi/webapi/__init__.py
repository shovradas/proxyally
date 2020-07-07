"""
ProxyAlly api package.
"""
from bson import ObjectId
from flask import Flask
from flask_restful import Api, abort
from flask_marshmallow import Marshmallow
from flask_pymongo import PyMongo
import pymongo
from webargs.flaskparser import parser
from flask_cors import CORS
from os import environ


def create_db_indexes_if_not_exists():
    # Checks if configurations exists, check id db exists as well
    if 'configurations' not in mongo.db.collection_names():
        mongo.db.providers.create_index('baseAddress', unique=True)
        mongo.db.proxies.create_index(
            [
                ("ip", pymongo.ASCENDING),
                ("port", pymongo.ASCENDING)
            ],
            unique=True
        )
        mongo.db.proxytesturls.create_index(
            [
                ("proxyId", pymongo.ASCENDING),
                ("testurlId", pymongo.ASCENDING)
            ],
            unique=True
        )
        mongo.db.testurls.create_index('url', unique=True)


def boot():
    err = True
    try:
        doc = mongo.db.configurations.find_one({'status': True})
        if doc:
            err = False
            print('Configuration: found')
    except:
        pass
    if err:
        create_db_indexes_if_not_exists()
        print('Configuration: missing')
        try:
            result = mongo.db.configurations.insert_one({
                "maxAge": 1,  # Week
                "syncInterval": 10,  # Minutes
                "downloadDelay": 1,  # Seconds
                "proxyTestTimeout": 1,  # Seconds
                "status": True
            })
            doc = mongo.db.configurations.find_one({'_id': result.inserted_id})
            mongo.db.configurations.update_many({'_id': {'$ne': ObjectId(doc['_id'])}}, {'$set': {'status': False}})

            print('Configuration: created')
        except:
            print('Boot: failed')
            abort(500, message='Boot: failed. could not be configured', status='error')

    print('Boot: successful')

app = Flask(__name__)

# CORS
cors = CORS(app, resources={r"/api/v1/*": {"origins": "*"}})

# MongoDB
app.config["MONGO_URI"] = environ.get('MONGO_URI', 'mongodb://localhost:27017/proxyAllyDB')
mongo = PyMongo(app)

boot()  # Check configurations or even DB exists

# Api
api = Api(app)

# Marshmallow
ma = Marshmallow(app)

from webapi.resources import *


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    abort(error_status_code, errors=err.messages)

