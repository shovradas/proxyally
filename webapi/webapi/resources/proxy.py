
from flask import url_for
from flask_restful import Resource, abort
from webargs.flaskparser import use_args
from marshmallow import fields
from bson.objectid import ObjectId
from webapi import api, mongo, ma
from webapi.common import util
from webapi.schemas import ProxySchema, ProxySchemaEmbedded, params_schema


proxy_schema = ProxySchema()
proxies_schema = ProxySchema(many=True)
proxy_schema_embedded = ProxySchemaEmbedded()
proxies_schema_embedded = ProxySchemaEmbedded(many=True)


@api.resource('/api/v1/proxies/<id>')
class Proxy(Resource):
    @use_args(params_schema, location="query")
    def get(self, args, id):
        util.abort_if_invalid_id_format(id)
        if args['embed']:
            docs = mongo.db.proxies.aggregate([
                {'$match': {'_id': ObjectId(id)}},
                {'$lookup': {'from': 'providers', 'localField': 'providerId', 'foreignField': '_id', 'as': 'provider'}},
                {'$unwind': '$provider'},
                {
                    '$lookup': {
                        'from': 'proxytesturls',
                        'let': { 'proxy_id': '$_id' },
                        'pipeline': [
			                { '$match': { '$expr': { '$eq': [ '$proxyId', '$$proxy_id' ] } } },
			                {
				                '$lookup': {
					                'from': 'testurls',
					                'let': { 'testurl_id': '$testurlId' },
					                'pipeline': [ { '$match': { '$expr': { '$eq': [ '$_id', '$$testurl_id' ] } } } ],
					                'as': 'testurl'
				                }
			                },
			                { '$unwind': '$testurl' },
			                { '$project' : { '_id': '$testurl._id', 'url' : '$testurl.url', 'description': '$testurl.description', 'urlFuncTestDate': '$urlFuncTestDate' } }
                        ],
                        'as': 'testurls'
                    }
                }
            ])
            docs=list(docs)
            util.abort_if_doesnt_exist(docs)
            return proxy_schema_embedded.dump(docs[0])

        doc = mongo.db.proxies.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return proxy_schema.dump(doc)
    
    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        mongo.db.proxies.delete_one({ '_id': ObjectId(id) })
        return '', 204

    @use_args(proxy_schema, location='json_or_form')
    def put(self, args, id):
        abort_if_provider_doesnt_exist(args['providerId'])
        util.abort_if_invalid_id_format(id)
        doc = mongo.db.proxies.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        mongo.db.proxies.update_one({ '_id': ObjectId(id) }, { '$set': args })
        return '', 204


@api.resource('/api/v1/proxies')
class ProxyList(Resource):
    @use_args(params_schema, location="query")
    def get(self, args):
        and_exprs = []
        if 'anonymities' in args:
            or_exprs = [{'anonymity': x} for x in args['anonymities'].split(',')]
            and_exprs.append({'$or': or_exprs})

        if 'providers' in args:
            or_exprs = [{'providerId': ObjectId(x)} for x in args['providers'].split(',')]
            and_exprs.append({'$or': or_exprs})

        final_expr = {}
        if and_exprs:
            final_expr = {'$and': and_exprs}

        util.var_dump(final_expr)

        if args['embed']:
            docs = mongo.db.proxies.aggregate([    
                {'$match': final_expr},
                {'$lookup': {'from': 'providers', 'localField': 'providerId', 'foreignField': '_id', 'as': 'provider'}},
                {'$unwind': '$provider'},
                {
                    '$lookup': {
                        'from': 'proxytesturls',
                        'let': { 'proxy_id': '$_id' },
                        'pipeline': [
			                { '$match': { '$expr': { '$eq': [ '$proxyId', '$$proxy_id' ] } } },
			                {
				                '$lookup': {
					                'from': 'testurls',
					                'let': { 'testurl_id': '$testurlId' },
					                'pipeline': [ { '$match': { '$expr': { '$eq': [ '$_id', '$$testurl_id' ] } } } ],
					                'as': 'testurl'
				                }
			                },
			                { '$unwind': '$testurl' },
			                { '$project' : { '_id': '$testurl._id', 'url' : '$testurl.url', 'url' : '$testurl.url', 'description': '$testurl.description', 'urlFuncTestDate': '$urlFuncTestDate' } }
                        ],
                        'as': 'testurls'
                    }
                },
                {'$skip' : args['offset']},
                {'$limit': args['limit']}          
            ])
            return proxies_schema_embedded.dump(docs)
        
        docs = mongo.db.proxies.find({anonymity: args['anonymity']}).skip(args['offset']).limit(args['limit'])
        return proxies_schema.dump(docs)

    @use_args(proxy_schema, location='json_or_form')
    def post(self, args):
        abort_if_provider_doesnt_exist(args['providerId'])
        doc = mongo.db.proxies.find_one({'ip': args['ip'], 'port': args['port']})
        if doc:
            mongo.db.proxies.update_one({ '_id': ObjectId(doc['_id']) }, { '$set': args })
            return '', 204
        else:
            result = mongo.db.proxies.insert_one(args)
            doc = mongo.db.proxies.find_one({'_id': result.inserted_id})
            return proxy_schema.dump(doc), 201, {'location': url_for('proxy', id=f'{result.inserted_id}')}


def abort_if_provider_doesnt_exist(providerId, **kwargs):
    provider = mongo.db.providers.find_one({'_id': ObjectId(providerId)})
    if provider is None:
        abort(422, message="Provider does not exists", status='error', **kwargs)