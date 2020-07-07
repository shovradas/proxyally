import os
import time
from flask import url_for, request
from flask_restful import Resource, abort
from webargs.flaskparser import use_args
from bson.objectid import ObjectId
from webapi import api, mongo, ma
from webapi.common import util
from webapi.schemas import ProviderSchema, ProviderSchemaEmbedded, ProviderSchemaCountEmbedded, params_schema
import datetime
from importlib import import_module
from core.proxy_checker import HttpProxyChecker
from urllib.parse import urlparse

provider_schema = ProviderSchema()
providers_schema = ProviderSchema(many=True)

provider_schema_embedded = ProviderSchemaEmbedded()
providers_schema_embedded = ProviderSchemaEmbedded(many=True)

provider_schema_count_embedded = ProviderSchemaCountEmbedded()
providers_schema_count_embedded = ProviderSchemaCountEmbedded(many=True)

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
        provider = mongo.db.providers.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(provider)

        #Clean proxytesturls
        proxies = mongo.db.proxies.find({'providerId': provider['_id']})
        for proxy in proxies:
            mongo.db.proxytesturls.delete_many({'proxyId': proxy['_id']})

        # Clean proxies
        mongo.db.proxies.delete_many({'providerId': provider['_id']})

        # Delete provider
        mongo.db.providers.delete_one({ '_id': provider['_id'] })
        return '', 204

    @use_args(provider_schema, location='json_or_form')
    @use_args(params_schema, location="query")
    def put(self, provider_new, params, id):
        util.abort_if_invalid_id_format(id)
        provider = mongo.db.providers.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(provider)

        for k, v in provider_new.items():
            provider[k] = v

        mongo.db.providers.update_one({ '_id': ObjectId(id) }, {'$set': provider})

        # Synchronising Proxy List based on syncTest param
        syncProxies(id, params['syncTest'])

        return '', 204

    def patch(self, id):
        util.abort_if_invalid_id_format(id)
        doc = mongo.db.providers.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        # Synchronising Proxy List
        syncProxies(id, 2)

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
            providers = mongo.db.providers.aggregate(pipeline)
            return providers_schema_embedded.dump(providers)

        providers = list(mongo.db.providers.find().skip(args['offset']).limit(args['limit']))
        # Embedding the proxy count
        for i in range(len(providers)):
            providers[i]['proxyCount'] = mongo.db.proxies.find({'providerId': providers[i]['_id']}).count()

        return providers_schema_count_embedded.dump(providers)

    @use_args(provider_schema, location='json_or_form')
    @use_args(params_schema, location="query")
    def post(self, provider, params):
        try:
            if provider['name'] == '':
                url = urlparse(provider['baseAddress'])
                provider['name'] = ''.join([c for c in url.hostname if c.isalpha()])
            insert_result = mongo.db.providers.insert_one(provider)
        except:
            abort(500, message="Could not create provider", status="error")  

        # Synchronising Proxy List based on syncTest param
        syncProxies(insert_result.inserted_id, params['syncTest'])
        provider = mongo.db.providers.find_one({'_id': insert_result.inserted_id})

        return provider_schema.dump(provider), 201, {'location': url_for('provider', id=provider['_id'])}

    def patch(self):
        providers = mongo.db.providers.find()

        for provider in providers:
            syncProxies(provider['_id'], 2)

        return '', 204


@api.resource('/api/v1/providers/fetchers')
class ProviderFetcher(Resource):
    def get(self):
        module = import_module(f'core.proxy_fetchers')
        func = getattr(module, 'get_fetcher_script_list')
        return func()

    def post(self):
        target_path = None
        try:
            file = request.files['fetcherScript']
            file_name, file_ext = file.filename.split('.')
            if file_ext != 'py':
                raise

            target_path = f'{os.getcwd()}/core/proxy_fetchers/{file.filename}'
            file.save(target_path)

            mdl = import_module(f'core.proxy_fetchers.{file_name}')
            getattr(mdl, 'fetch')  # Throws exception if not exists
        except:
            if target_path and os.path.exists(target_path):
                os.remove(target_path)
            abort(500, message="Only alphanumeric name supported and script should contain a fetch() method", status="error")

        return '', 201


def syncProxies(providerId, syncTest):
    provider = mongo.db.providers.find_one({'_id': ObjectId(providerId)})
    util.abort_if_doesnt_exist(provider)

    if provider["fetcher"] == 'None':
         return

    # Checking update interval
    cfg = mongo.db.configurations.find_one({'status': True})
    if not cfg:
        cfg = {
            'syncInterval': 10,
            'maxAge': 1,
            'downloadDelay': 1,
            'proxyTestTimeout': 1
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
        # Delete stale proxies #############################################
        stale_expr_1 = {
            'providerId': provider['_id'],
            'funcTestDate': {'$exists': False}
        }
        stale_expr_2 = {
            'providerId': provider['_id'],
            'funcTestDate': {'$exists': True},
            'funcTestDate': {'$lte': (datetime.datetime.now() - datetime.timedelta(weeks=cfg['maxAge']))}
        }
        stale_expr_final = {'$or': [stale_expr_1, stale_expr_2]}
        #print(stale_expr_final)

        try:
            stale_proxies = list(mongo.db.proxies.find(stale_expr_final))
            #print(len(stale_proxies))
            for sp in stale_proxies:
                mongo.db.proxytesturls.delete_many({'proxyId': sp['_id']})
            mongo.db.proxies.delete_many(stale_expr_final)
            #print(len(list(mongo.db.proxies.find(stale_expr_final))))
            #return
        except Exception as err:
            print(err)
            pass
        ###################################################################

        try:
            mdl = import_module(f'core.proxy_fetchers.{provider["fetcher"]}')            
            fetch = getattr(mdl, 'fetch')          
            fetchedProxies = fetch(config=cfg)
            proxies = fetchedProxies # updating with fetched proxies
            provider['updateAttempt'] = {'type':'fetch', 'status':'success', 'proxyCount': len(fetchedProxies), 'attemptDate': datetime.datetime.now()}
        except Exception as err:
            print(err)
            provider['updateAttempt'] = {'type':'fetch', 'status':'failed', 'message':'Error occurred while fetching', 'attemptDate': datetime.datetime.now()}

        if provider['updateAttempt']['status']=='success':
            # Attempting to test
            if syncTest==2:
                proxyChecker = HttpProxyChecker()
                checkedProxies = []
                try:
                    for proxy in fetchedProxies:
                        checkResult = proxyChecker.check_proxy(f"{proxy['ip']}:{proxy['port']}", cfg['proxyTestTimeout'])
                        if checkResult['status']=='online':
                            proxy['anonymity'] = checkResult['anonymity']
                            #proxy['country'] = checkResult['country']
                            #proxy['timeout'] = checkResult['timeout']
                            proxy['funcTestDate'] = datetime.datetime.now()                                                
                            checkedProxies.append(proxy)
                    proxies = checkedProxies # updating with online proxies
                    provider['updateAttempt'] = {'type':'funcTest', 'status':'success', 'proxyCount': len(checkedProxies), 'attemptDate': datetime.datetime.now()}
                except Exception as err:
                    print(err)
                    provider['updateAttempt'] = {'type':'funcTest', 'status':'failed', 'message':'Error occurred while testing basic functionality', 'attemptDate': datetime.datetime.now()}
            
            #util.var_dump(len(proxies))
            for proxy in proxies:
                proxy['providerId'] = provider['_id']
                proxy['lastFoundDate'] = datetime.datetime.now()                    
                try:
                    result = mongo.db.proxies.update_one({'ip': proxy['ip'], 'port': proxy['port']}, {'$set': proxy})
                    # print('modified count: ', result.modified_count)
                    if result.modified_count == 0:
                        raise Exception("Could not update")
                except:
                    try:
                        proxy['discoveredDate'] = datetime.datetime.now()
                        result = mongo.db.proxies.insert_one(proxy)
                        # print('inserted')
                    except:
                        continue
                
            proxyCount = mongo.db.proxies.count({'providerId': provider['_id']})
            #util.var_dump(proxyCount)
            if proxyCount==0:
                provider['updateAttempt'] = {'type': f'syncDB_{provider["updateAttempt"]["type"]}', 'status':'failed', 'message':'No proxy is functional or error occurred while updating database', 'attemptDate': datetime.datetime.now()}
            elif proxyCount == len(proxies):
                provider['updateAttempt'] = {'type': f'syncDB_{provider["updateAttempt"]["type"]}', 'status':'success', 'proxyCount': proxyCount, 'attemptDate': datetime.datetime.now()}
            else:
                provider['updateAttempt'] = {'type': f'syncDB_{provider["updateAttempt"]["type"]}', 'status':'partial', 'proxyCount': proxyCount, 'message':'Some proxies ar not functional or duplicate found', 'attemptDate': datetime.datetime.now()}

        mongo.db.providers.update_one({ '_id': provider['_id'] }, {'$set': provider})