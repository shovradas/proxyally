
from flask import url_for
from flask_restful import Resource
from webargs.flaskparser import use_args
from marshmallow import fields, post_dump
from bson.objectid import ObjectId
from webapi import api, mongo
from webapi.common import util
from webapi.schemas import TesturlSchema, TesturlSchemaEmbedded, params_schema


testurl_schema = TesturlSchema()
testurls_schema = TesturlSchema(many=True)

testurl_schema_embedded = TesturlSchemaEmbedded()
testurls_schema_embedded = TesturlSchemaEmbedded(many=True)

@api.resource('/api/v1/testurls/<id>')
class TestUrl(Resource):
    @use_args(params_schema, location="query")
    def get(self, args, id):
        util.abort_if_invalid_id_format(id)
        if args['embed']:
            docs = mongo.db.testurls.aggregate([
                {'$match': {'_id': ObjectId(id)}},
                {                    
                    "$lookup": {
                        "from": "proxytesturls",
                        "let": { "testurl_id": "$_id" },
                        "pipeline": [{ "$match": { "$expr": { "$eq": ["$testurlId", "$$testurl_id"] } } },
			                {
				                "$lookup": {
					                "from": "proxies",
					                "let": { "proxy_id": "$proxyId" },
					                "pipeline": [{ "$match": { "$expr": { "$eq": ["$_id", "$$proxy_id"] } } }],
					                "as": "proxy"
				                }
			                },
			                { "$unwind": "$proxy" },
			                { 
				                "$project" : { 
					                "_id": "$proxy._id",
					                "providerId": "$proxy.providerId",
					                "ip": "$proxy.ip",
					                "port": "$proxy.port",
					                "funcTestDate": "$proxy.funcTestDate",
					                "lastFoundDate": "$proxy.lastFoundDate",
					                "discoveredDate": "$proxy.discoveredDate",
					                "anonymity": "$proxy.anonymity",
					                "urlFuncTestDate": "$urlFuncTestDate"
				                } 
			                }],
                        "as": "proxies"
                    }
                }
            ])
            docs=list(docs)
            util.abort_if_doesnt_exist(docs)
            return testurl_schema_embedded.dump(docs[0])

        doc = mongo.db.testurls.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return testurl_schema.dump(doc)
    
    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        mongo.db.proxytesturls.delete_many({'testurlId': ObjectId(id)})
        mongo.db.testurls.delete_one({ '_id': ObjectId(id) })
        return '', 204

    @use_args(testurl_schema, location='json_or_form')
    def put(self, args, id):
        util.abort_if_invalid_id_format(id)
        doc = mongo.db.testurls.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)   
        mongo.db.testurls.update_one({ '_id': ObjectId(id) }, { '$set': args })
        return '', 204


@api.resource('/api/v1/testurls')
class TestUrlList(Resource):
    @use_args(params_schema, location="query")
    def get(self, args):
        if args['embed']:
            docs = mongo.db.testurls.aggregate([
                {
                    "$lookup": {
                        "from": "proxytesturls",
                        "let": { "testurl_id": "$_id" },
                        "pipeline": [{ "$match": { "$expr": { "$eq": ["$testurlId", "$$testurl_id"] } } },
			                {
				                "$lookup": {
					                "from": "proxies",
					                "let": { "proxy_id": "$proxyId" },
					                "pipeline": [{ "$match": { "$expr": { "$eq": ["$_id", "$$proxy_id"] } } }],
					                "as": "proxy"
				                }
			                },
			                { "$unwind": "$proxy" },
			                { 
				                "$project" : { 
					                "_id": "$proxy._id",
					                "providerId": "$proxy.providerId",
					                "ip": "$proxy.ip",
					                "port": "$proxy.port",
					                "funcTestDate": "$proxy.funcTestDate",
					                "lastFoundDate": "$proxy.lastFoundDate",
					                "discoveredDate": "$proxy.discoveredDate",
					                "anonymity": "$proxy.anonymity",
					                "urlFuncTestDate": "$urlFuncTestDate"
				                } 
			                }],
                        "as": "proxies"
                    }
                },                
                {'$skip' : args['offset']},
                {'$limit': args['limit']}
            ])
            return testurls_schema_embedded.dump(docs)

        docs = mongo.db.testurls.find().skip(args['offset']).limit(args['limit'])   
        return testurls_schema.dump(docs)

    @use_args(testurl_schema, location='json_or_form')
    def post(self, args):
        result = mongo.db.testurls.insert_one(args)
        doc = mongo.db.testurls.find_one({'_id': result.inserted_id})
        return testurl_schema.dump(doc), 201, {'location': url_for('testurl', id=f'{result.inserted_id}')}