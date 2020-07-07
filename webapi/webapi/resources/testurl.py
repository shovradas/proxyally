import datetime
import time

from flask import url_for
from flask_restful import Resource, abort
from webargs.flaskparser import use_args
from bson.objectid import ObjectId
from core.proxy_checker import HttpProxyChecker
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
                        "let": {"testurl_id": "$_id"},
                        "pipeline": [{"$match": {"$expr": {"$eq": ["$testurlId", "$$testurl_id"]}}},
                                     {
                                         "$lookup": {
                                             "from": "proxies",
                                             "let": {"proxy_id": "$proxyId"},
                                             "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$proxy_id"]}}}],
                                             "as": "proxy"
                                         }
                                     },
                                     {"$unwind": "$proxy"},
                                     {
                                         "$project": {
                                             "_id": "$proxy._id",
                                             "providerId": "$proxy.providerId",
                                             "ip": "$proxy.ip",
                                             "port": "$proxy.port",
                                             "funcTestDate": "$proxy.funcTestDate",
                                             "lastFoundDate": "$proxy.lastFoundDate",
                                             "discoveredDate": "$proxy.discoveredDate",
                                             "anonymity": "$proxy.anonymity",
                                             "validationTestDate": "$validationTestDate",
                                             "validationTestStatus": "$validationTestStatus"
                                         }
                                     }],
                        "as": "proxies"
                    }
                }
            ])
            docs = list(docs)
            util.abort_if_doesnt_exist(docs)
            return testurl_schema_embedded.dump(docs[0])

        doc = mongo.db.testurls.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return testurl_schema.dump(doc)

    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        mongo.db.proxytesturls.delete_many({'testurlId': ObjectId(id)})
        mongo.db.testurls.delete_one({'_id': ObjectId(id)})
        return '', 204

    @use_args(testurl_schema, location='json_or_form')
    @use_args(params_schema, location="query")
    def put(self, testurl_new, params, id):
        util.abort_if_invalid_id_format(id)
        testurl = mongo.db.testurls.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(testurl)

        for k, v in testurl_new.items():
            testurl[k] = v

        mongo.db.testurls.update_one({'_id': ObjectId(id)}, {'$set': testurl})

        if params['validate']:
            validate_testurl(testurl['_id'])

        return '', 204

    def patch(self, id):
        util.abort_if_invalid_id_format(id)

        if not validate_testurl(id):
            abort(500, message='Error occurred while syncing', status="error")

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
                        "let": {"testurl_id": "$_id"},
                        "pipeline": [{"$match": {"$expr": {"$eq": ["$testurlId", "$$testurl_id"]}}},
                                     {
                                         "$lookup": {
                                             "from": "proxies",
                                             "let": {"proxy_id": "$proxyId"},
                                             "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$proxy_id"]}}}],
                                             "as": "proxy"
                                         }
                                     },
                                     {"$unwind": "$proxy"},
                                     {
                                         "$project": {
                                             "_id": "$proxy._id",
                                             "providerId": "$proxy.providerId",
                                             "ip": "$proxy.ip",
                                             "port": "$proxy.port",
                                             "funcTestDate": "$proxy.funcTestDate",
                                             "lastFoundDate": "$proxy.lastFoundDate",
                                             "discoveredDate": "$proxy.discoveredDate",
                                             "anonymity": "$proxy.anonymity",
                                             "validationTestDate": "$validationTestDate",
                                             "validationTestStatus": "$validationTestStatus"
                                         }
                                     }],
                        "as": "proxies"
                    }
                },
                {'$skip': args['offset']},
                {'$limit': args['limit']}
            ])
            return testurls_schema_embedded.dump(docs)

        docs = mongo.db.testurls.find().skip(args['offset']).limit(args['limit'])
        return testurls_schema.dump(docs)

    @use_args(testurl_schema, location='json_or_form')
    @use_args(params_schema, location="query")
    def post(self, testurl, params):
        result = mongo.db.testurls.insert_one(testurl)
        testurl = mongo.db.testurls.find_one({'_id': result.inserted_id})
        if params['validate']:
            validate_testurl(testurl['_id'])
        return testurl_schema.dump(testurl), 201, {'location': url_for('testurl', id=testurl['_id'])}

    def patch(self):
        testurls = mongo.db.testurls.find()
        for testurl in testurls:
            validate_testurl(testurl['_id'])
        return '', 204


def validate_testurl(testurl_id):
    testurl = mongo.db.testurls.find_one({'_id': ObjectId(testurl_id)})
    util.abort_if_doesnt_exist(testurl)

    cfg = mongo.db.configurations.find_one({'status': True})
    if not cfg:
        cfg = {
            'syncInterval': 10,
            'maxAge': 1,
            'downloadDelay': 1,
            'proxyTestTimeout': 1
        }

    proxies = list(mongo.db.proxies.find())
    proxy_checker = HttpProxyChecker()
    valid_proxy_count = 0
    for proxy in proxies:
        try:
            proxy_address = f"{proxy['ip']}:{proxy['port']}"
            # Checking if online
            result = proxy_checker.check_proxy(proxy_address, cfg['proxyTestTimeout'])
            if result['status'] == 'online':
                proxy['anonymity'] = result['anonymity']
                proxy['funcTestDate'] = datetime.datetime.now()
                try:
                    mongo.db.proxies.update_one({'_id': proxy['_id']}, {'$set': proxy})
                except:
                    print('error: while syncing proxy')
                    continue
            else:
                try:
                    mongo.db.proxytesturls.delete_many({'proxyId': proxy['_id']})
                    mongo.db.proxies.delete_one({'_id': proxy['_id']})
                    continue
                except:
                    print('error: while deleting proxy')
                    continue
            ###############

            # Validating
            result = proxy_checker.validate_proxy(proxy_address, testurl['url'], cfg['proxyTestTimeout'])
            proxytesturl = {
                'proxyId': proxy['_id'],
                'testurlId': testurl['_id'],
                'validationTestDate': datetime.datetime.now(),
                'validationTestStatus': result['status']
            }
            mongo.db.proxytesturls.update_one(
                {'proxyId': proxy['_id'], 'testurlId': testurl['_id']},
                {'$set': proxytesturl},
                upsert=True
            )
            if result['status'] == 'success':
                valid_proxy_count += 1
        except:
            print('error: validate_testurl')
            continue
    try:
        testurl['validationAttempt'] = {
            'attemptDate': datetime.datetime.now(),
            'validProxyCount': valid_proxy_count,
            'status': 'success' if (valid_proxy_count !=0 and valid_proxy_count == len(proxies)) else ('partial' if valid_proxy_count>0 else 'failed')
        }
        mongo.db.testurls.update_one({'_id': testurl['_id']}, {'$set': testurl})
        return True
    except:
        return False
