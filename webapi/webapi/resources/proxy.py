import datetime

from flask import url_for
from flask_restful import Resource, abort
from webargs.flaskparser import use_args
from core.proxy_checker import HttpProxyChecker
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
                        'let': {'proxy_id': '$_id'},
                        'pipeline': [
                            {'$match': {'$expr': {'$eq': ['$proxyId', '$$proxy_id']}}},
                            {
                                '$lookup': {
                                    'from': 'testurls',
                                    'let': {'testurl_id': '$testurlId'},
                                    'pipeline': [{'$match': {'$expr': {'$eq': ['$_id', '$$testurl_id']}}}],
                                    'as': 'testurl'
                                }
                            },
                            {'$unwind': '$testurl'},
                            {'$project': {'_id': '$testurl._id', 'url': '$testurl.url',
                                          'validationAttempt': '$testurl.validationAttempt', 'validationTestDate': '$validationTestDate', 'validationTestStatus': '$validationTestStatus'}}
                        ],
                        'as': 'testurls'
                    }
                }
            ])
            docs = list(docs)
            util.abort_if_doesnt_exist(docs)
            return proxy_schema_embedded.dump(docs[0])

        doc = mongo.db.proxies.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return proxy_schema.dump(doc)

    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        mongo.db.proxytesturls.delete_many({'proxyId': ObjectId(id)})
        mongo.db.proxies.delete_one({'_id': ObjectId(id)})
        return '', 204

    @use_args(proxy_schema, location='json_or_form')
    def put(self, proxy_new, id):
        abort_if_provider_doesnt_exist(proxy_new['providerId'])
        util.abort_if_invalid_id_format(id)
        proxy = mongo.db.proxies.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(proxy)

        for k, v in proxy_new.items():
            proxy[k] = v

        mongo.db.proxies.update_one({'_id': ObjectId(id)}, {'$set': proxy})
        return '', 204

    @use_args(params_schema, location="query")
    def patch(self, args, id):
        util.abort_if_invalid_id_format(id)

        if sync_proxy(id):
            if args['validate']:
                validate_proxy(id)
        else:
            abort(404, message='This proxy is currently offline, hence removed', status="error")
        return '', 204


@api.resource('/api/v1/proxies')
class ProxyList(Resource):
    @use_args(params_schema, location="query")
    def get(self, args):
        and_exprs = []
        if 'anonymities' in args:
            or_exprs = [{'anonymity': x if x!='Unknown' else None} for x in args['anonymities'].split(',')]
            #or_exprs.append({'anonymity': None}) # If Anonymity is missing
            and_exprs.append({'$or': or_exprs})

        if 'providers' in args:
            if args['providers'] == 'None':
                or_exprs = [{'providerId': 'None'}]
            else:
                or_exprs = [{'providerId': ObjectId(x)} for x in args['providers'].split(',')]
            and_exprs.append({'$or': or_exprs})

        final_expr = {}
        if and_exprs:
            final_expr = {'$and': and_exprs}

        util.var_dump(final_expr)

        if 'sort' not in args:
            args['sort'] = 'funcTestDate'
        if 'order' not in args:
            args['order'] = -1

        print({'$sort': {args['sort']: args['order']}})

        if args['embed']:
            docs = mongo.db.proxies.aggregate([
                {'$match': final_expr},
                {'$lookup': {'from': 'providers', 'localField': 'providerId', 'foreignField': '_id', 'as': 'provider'}},
                {'$unwind': '$provider'},
                {
                    '$lookup': {
                        'from': 'proxytesturls',
                        'let': {'proxy_id': '$_id'},
                        'pipeline': [
                            {'$match': {'$expr': {'$eq': ['$proxyId', '$$proxy_id']}}},
                            {
                                '$lookup': {
                                    'from': 'testurls',
                                    'let': {'testurl_id': '$testurlId'},
                                    'pipeline': [{'$match': {'$expr': {'$eq': ['$_id', '$$testurl_id']}}}],
                                    'as': 'testurl'
                                }
                            },
                            {'$unwind': '$testurl'},
                            {'$project': {'_id': '$testurl._id', 'url': '$testurl.url', 'url': '$testurl.url',
                                          'validationAttempt': '$testurl.validationAttempt', 'validationTestDate': '$validationTestDate', 'validationTestStatus': '$validationTestStatus'}}
                        ],
                        'as': 'testurls'
                    }
                },
                {'$sort': {args['sort']: int(args['order'])}},
                {'$skip': args['offset']},
                {'$limit': args['limit']}
            ])

            # count_query = mongo.db.proxies.aggregate([
            #     {'$match': final_expr},
            #     {'$lookup': {'from': 'providers', 'localField': 'providerId', 'foreignField': '_id', 'as': 'provider'}},
            #     {'$unwind': '$provider'},
            #     {
            #         '$lookup': {
            #             'from': 'proxytesturls',
            #             'let': {'proxy_id': '$_id'},
            #             'pipeline': [
            #                 {'$match': {'$expr': {'$eq': ['$proxyId', '$$proxy_id']}}},
            #                 {
            #                     '$lookup': {
            #                         'from': 'testurls',
            #                         'let': {'testurl_id': '$testurlId'},
            #                         'pipeline': [{'$match': {'$expr': {'$eq': ['$_id', '$$testurl_id']}}}],
            #                         'as': 'testurl'
            #                     }
            #                 },
            #                 {'$unwind': '$testurl'},
            #                 {'$project': {'_id': '$testurl._id', 'url': '$testurl.url', 'url': '$testurl.url',
            #                               'validationAttempt': '$testurl.validationAttempt',
            #                               'validationTestDate': '$validationTestDate',
            #                               'validationTestStatus': '$validationTestStatus'}}
            #             ],
            #             'as': 'testurls'
            #         }
            #     },
            #     {'$count': 'ip'},
            #     {'$project': {'totalCount': '$ip'}}
            # ])
            #
            # totalCount = list(count_query)[0]['totalCount']
            # print(totalCount)

            totalCount = mongo.db.proxies.find(final_expr).count()
            final_doc = proxies_schema_embedded.dump(docs)
            final_doc['totalCount'] = totalCount
            #print(final_doc)
            # return proxies_schema_embedded.dump(docs)
            return final_doc

        # docs = mongo.db.proxies.find(final_expr).skip(args['offset']).limit(args['limit'])
        docs = mongo.db.proxies.find(final_expr)
        totalCount = docs.count()
        print(totalCount)
        docs = docs.skip(args['offset']).limit(args['limit'])
        final_doc = proxies_schema.dump(docs)
        final_doc['totalCount'] = totalCount
        # return proxies_schema.dump(docs)
        return final_doc

    @use_args(proxy_schema, location='json_or_form')
    def post(self, args):
        abort_if_provider_doesnt_exist(args['providerId'])
        doc = mongo.db.proxies.find_one({'ip': args['ip'], 'port': args['port']})
        if doc:
            mongo.db.proxies.update_one({'_id': ObjectId(doc['_id'])}, {'$set': args})
            return '', 204
        else:
            result = mongo.db.proxies.insert_one(args)
            doc = mongo.db.proxies.find_one({'_id': result.inserted_id})
            return proxy_schema.dump(doc), 201, {'location': url_for('proxy', id=f'{result.inserted_id}')}


def abort_if_provider_doesnt_exist(providerId, **kwargs):
    provider = mongo.db.providers.find_one({'_id': ObjectId(providerId)})
    if provider is None:
        abort(422, message="Provider does not exists", status='error', **kwargs)


def sync_proxy(proxy_id):
    proxy = mongo.db.proxies.find_one({'_id': ObjectId(proxy_id)})
    util.abort_if_doesnt_exist(proxy)

    cfg = mongo.db.configurations.find_one({'status': True})
    if not cfg:
        cfg = {
            'syncInterval': 10,
            'maxAge': 1,
            'downloadDelay': 1,
            'proxyTestTimeout': 1
        }

    proxy_checker = HttpProxyChecker()
    result = proxy_checker.check_proxy(f"{proxy['ip']}:{proxy['port']}", cfg['proxyTestTimeout'])
    if result['status'] == 'online':
        proxy['anonymity'] = result['anonymity']
        proxy['funcTestDate'] = datetime.datetime.now()
        try:
            mongo.db.proxies.update_one({'_id': proxy['_id']}, {'$set': proxy})
            return True
        except:
            abort(500, message='Error occurred while syncing', status="error")
    else:
        try:
            mongo.db.proxytesturls.delete_many({'proxyId': proxy['_id']})
            mongo.db.proxies.delete_one({'_id': proxy['_id']})
        except:
            abort(500, message='Error occurred while syncing', status="error")
        return False


def validate_proxy(proxy_id):
    proxy = mongo.db.proxies.find_one({'_id': ObjectId(proxy_id)})
    util.abort_if_doesnt_exist(proxy)

    cfg = mongo.db.configurations.find_one({'status': True})
    if not cfg:
        cfg = {
            'syncInterval': 10,
            'maxAge': 1,
            'downloadDelay': 1,
            'proxyTestTimeout': 1
        }

    testurls = mongo.db.testurls.find()
    proxy_checker = HttpProxyChecker()
    for testurl in testurls:
        try:
            result = proxy_checker.validate_proxy(f"{proxy['ip']}:{proxy['port']}", testurl['url'], cfg['proxyTestTimeout'])
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
        except:
            print('error: validate_proxy')
            continue