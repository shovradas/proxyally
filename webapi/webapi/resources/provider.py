
from flask import url_for
from flask_restful import Resource, abort
from webargs.flaskparser import use_args
from marshmallow import fields
from bson.objectid import ObjectId
from webapi import api, mongo, ma
from webapi.common import util
from webapi.schemas import ProviderSchema, ProviderSchemaEmbedded, params_schema
import datetime
from importlib import import_module
import os
from core.proxy_checker import HttpProxyChecker


provider_schema = ProviderSchema()
providers_schema = ProviderSchema(many=True)

provider_schema_embedded = ProviderSchemaEmbedded()
providers_schema_embedded = ProviderSchemaEmbedded(many=True)


@api.resource('/api/v1/providers/<id>')
class Provider(Resource):
    @use_args(params_schema, location="query")
    def get(self, args, id):
        util.abort_if_invalid_id_format(id)
        if args['embed']:
            pipeline = [
                {'$match': {'_id': ObjectId(id)}},
                {'$lookup': {'from': 'proxies', 'localField': '_id', 'foreignField': 'providerId', 'as': 'proxies'}},
            ]
            docs = list(mongo.db.providers.aggregate(pipeline)) # pymongo aggregate returns list
            util.abort_if_doesnt_exist(docs)
            return provider_schema_embedded.dump(docs[0])

        doc = mongo.db.providers.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return provider_schema.dump(doc)
    
    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        #TODO: Clean proxytesturl
        mongo.db.proxies.delete_many({'providerId': ObjectId(id)})
        mongo.db.providers.delete_one({ '_id': ObjectId(id) })
        return '', 204

    @use_args(provider_schema, location='json_or_form')
    @use_args(params_schema, location="query")
    def put(self, args, params, id):
        util.abort_if_invalid_id_format(id)
        doc = mongo.db.providers.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)   
        mongo.db.providers.update_one({ '_id': ObjectId(id) }, { '$set': args })

        # Synchronising Proxy List based on syncTest param
        syncProxies(id, params['syncTest'])

        return '', 204


@api.resource('/api/v1/providers')
class ProviderList(Resource):
    @use_args(params_schema, location="query")
    def get(self, args):
        if args['embed']:
            pipeline = [
                {'$lookup': {'from': 'proxies', 'localField': '_id', 'foreignField': 'providerId', 'as': 'proxies'}},                
                {'$skip' : args['offset']},
                {'$limit': args['limit']}
            ]
            docs = mongo.db.providers.aggregate(pipeline)
            return providers_schema_embedded.dump(docs)

        docs = mongo.db.providers.find().skip(args['offset']).limit(args['limit'])
        return providers_schema.dump(docs)

    @use_args(provider_schema, location='json_or_form')
    @use_args(params_schema, location="query")
    def post(self, provider, params):
        try:
            insert_result = mongo.db.providers.insert_one(provider)
        except:
            abort(500, message="Could not create provider", status="error")  

        # Synchronising Proxy List based on syncTest param
        syncProxies(insert_result.inserted_id, params['syncTest'])
        provider = mongo.db.providers.find_one({'_id': insert_result.inserted_id})

        return provider_schema.dump(provider), 201, {'location': url_for('provider', id=provider['_id'])}



def syncProxies(providerId, syncTest):
    provider = mongo.db.providers.find_one({'_id': ObjectId(providerId)})
    util.abort_if_doesnt_exist(provider)

    # Checking update interval
    cfg = mongo.db.configurations.find_one({'status': True})
    if not cfg:
        cfg = {
            'syncInterval': 10,
            'maxAge': 1
        }

    if 'updateAttempt' in provider:
        duration = datetime.datetime.now() - provider['updateAttempt']['attemptDate']
        syncInterval = datetime.timedelta(0, 0, 0, 0, cfg['syncInterval'], 0, 0)        
        if duration<syncInterval:
            abort(429, message="Too many requests,. You can change the interval from settings section", status="error")
    
    proxies=[]
    #print(provider)
    # Attempting to fetch
    if syncTest in [1, 2]: # 0->save only, 1-> fetch only, 2-> fetch+test        
        
        # Delete stale proxies
        expr = {
            'providerId': provider['_id'],
            'funcTestDate': {'$exists': False},
            'lastFoundDate': {'$gte': f'new Date(new Date() - {cfg["maxAge"]} * 7 * 60 * 60 * 24 * 1000)' }
        }
        print(expr)
        mongo.db.proxies.delete_many(expr)


        try:                
            mdl = import_module(f'core.proxy_fetchers.{provider["fetcher"]}')            
            fetch = getattr(mdl, 'fetch')          
            fetchedProxies = fetch()
            proxies = fetchedProxies # updating with fetched proxies
            provider['updateAttempt'] = {'type':'fetch', 'status':'success', 'proxyCount': len(fetchedProxies), 'attemptDate': datetime.datetime.now()}
        except:
            provider['updateAttempt'] = {'type':'fetch', 'status':'failed', 'message':'Error occured while fetching', 'attemptDate': datetime.datetime.now()}

        if provider['updateAttempt']['status']=='success':
            # Attempting to test
            if syncTest==2:
                proxyChecker = HttpProxyChecker()
                checkedProxies = []
                try:
                    for proxy in fetchedProxies[:10]:
                        checkResult = proxyChecker.check_proxy(f"{proxy['ip']}:{proxy['port']}") 
                        if(checkResult['status']=='online'):
                            proxy['anonymity'] = checkResult['anonymity']
                            #proxy['country'] = checkResult['country']
                            #proxy['timeout'] = checkResult['timeout']
                            proxy['funcTestDate'] = datetime.datetime.now()                                                
                            checkedProxies.append(proxy)
                    proxies = checkedProxies # updating with online proxies
                    provider['updateAttempt'] = {'type':'funcTest', 'status':'success', 'proxyCount': len(checkedProxies), 'attemptDate': datetime.datetime.now()}
                except:
                    provider['updateAttempt'] = {'type':'funcTest', 'status':'failed', 'message':'Error occured while basic functionality testing', 'attemptDate': datetime.datetime.now()}
            
            util.var_dump(len(proxies))
            for proxy in proxies:
                proxy['providerId'] = provider['_id']
                proxy['lastFoundDate'] = datetime.datetime.now()                    
                try:
                    result = mongo.db.proxies.update_one({'ip': proxy['ip'], 'port': proxy['port']}, {'$set': proxy})
                    print('modified', result.modified_count)
                    if result.modified_count==0:
                        raise Exception("Could not update")
                except:
                    try:                            
                        proxy['discoveredDate'] = datetime.datetime.now()
                        result = mongo.db.proxies.insert_one(proxy)
                        print('inserted_count: ', result.inserted_count)
                    except:                            
                        continue
                
            proxyCount = mongo.db.proxies.count({'providerId': provider['_id']})
            util.var_dump(proxyCount)
            if proxyCount==0:
                provider['updateAttempt'] = {'type': f'syncDB_{provider["updateAttempt"]["type"]}', 'status':'failed', 'message':'Error occured while updating database', 'attemptDate': datetime.datetime.now()}
            elif proxyCount == len(proxies):
                provider['updateAttempt'] = {'type': f'syncDB_{provider["updateAttempt"]["type"]}', 'status':'success', 'proxyCount': proxyCount, 'attemptDate': datetime.datetime.now()}
            else:
                provider['updateAttempt'] = {'type': f'syncDB_{provider["updateAttempt"]["type"]}', 'status':'partial', 'proxyCount': proxyCount, 'message':'Error occured while updating database', 'attemptDate': datetime.datetime.now()}

        mongo.db.providers.update_one({ '_id': provider['_id'] }, {'$set': provider})