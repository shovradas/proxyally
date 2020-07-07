
from flask import url_for
from flask_restful import Resource
from webargs.flaskparser import use_args
from marshmallow import fields, post_dump
from bson.objectid import ObjectId
from webapi import api, mongo
from webapi.common import util
from webapi.schemas import ConfigurationSchema, params_schema


configuration_schema = ConfigurationSchema()
configurations_schema = ConfigurationSchema(many=True)


@api.resource('/api/v1/configurations/<id>')
class Configuration(Resource):
    def get(self, id):
        util.abort_if_invalid_id_format(id)
        doc = mongo.db.configurations.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return configuration_schema.dump(doc)
    
    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        mongo.db.configurations.delete_one({ '_id': ObjectId(id) })
        return '', 204

    @use_args(configuration_schema, location='json_or_form')
    def put(self, configuration_new, id):
        util.abort_if_invalid_id_format(id)
        configuration = mongo.db.configurations.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(configuration)

        for k, v in configuration_new.items():
            configuration[k] = v

        result = mongo.db.configurations.update_one({ '_id': ObjectId(id) }, { '$set': configuration })
        if result.modified_count !=0 and configuration['status']:
            mongo.db.configurations.update_many({'_id': {'$ne': ObjectId(id)}}, {'$set': {'status': False}})

        return '', 204


@api.resource('/api/v1/configurations')
class ConfigurationList(Resource):
    @use_args(params_schema, location="query")
    def get(self, args):
        docs = mongo.db.configurations.find().skip(args['offset']).limit(args['limit'])   
        return configurations_schema.dump(docs)

    @use_args(configuration_schema, location='json_or_form')
    def post(self, args):
        result = mongo.db.configurations.insert_one(args)
        doc = mongo.db.configurations.find_one({'_id': result.inserted_id})
        if doc and args['status']:
            mongo.db.configurations.update_many({'_id': {'$ne': ObjectId(doc['_id'])}}, {'$set': {'status': False}})
        return configuration_schema.dump(doc), 201, {'location': url_for('configuration', id=f'{result.inserted_id}')}


@api.resource('/api/v1/configurations/current')
class ConfigurationCurrent(Resource):
    def get(self):
        doc = mongo.db.configurations.find_one({'status': True})
        util.abort_if_doesnt_exist(doc)
        return configuration_schema.dump(doc)

    @use_args(configuration_schema, location='json_or_form')
    def put(self, configuration_new):
        configuration = mongo.db.configurations.find_one({'status': True})
        util.abort_if_doesnt_exist(configuration)

        for k, v in configuration_new.items():
            configuration[k] = v

        result = mongo.db.configurations.update_one({'_id': configuration['_id']}, {'$set': configuration})
        if result.modified_count != 0 and configuration['status']:
            mongo.db.configurations.update_many({'_id': {'$ne': configuration['_id']}}, {'$set': {'status': False}})

        return '', 204