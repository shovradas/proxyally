import sys

from marshmallow import fields, post_dump, validate
from webapi import ma
from webapi.common import util
import webargs


# region marshmallow_schemas

class BaseSchema(ma.Schema):
    class Meta:
        #dateformat = '%Y-%m-%dT%H:%M:%S+03:00'
        dateformat = '%Y-%m-%dT%H:%M:%S'
        ordered = True

    _id = util.CustomObjectIdField(data_key='id', dump_only=True)

    @post_dump(pass_many=True)
    def add_meta_fields(self, data, many, **kwargs):      
        data = {'count': len(data), 'items': data} if many else data
        return data


class TesturlSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('_links', '_id', 'url', 'validationAttempt')

    _id = util.CustomObjectIdField(data_key='id', dump_only=True)
    url = fields.String(required=True, validate=validate.Length(min=10))
    validationAttempt = fields.Dict(keys=fields.Str(), values=fields.Str(), dump_only=True)

    _links = ma.Hyperlinks({
        'self': {
            'href': ma.AbsoluteURLFor('testurl', id='<_id>'),
            'title': 'test-url detail'
        },
        'collection': {
           'href': ma.AbsoluteURLFor('testurllist'),           
           'title': 'list of test urls'
        }
    })
    

class ProxyTesturlSchema(TesturlSchema):
    class Meta(TesturlSchema.Meta):
        fields = ('_links', '_id', 'url', 'validationAttempt', 'validationTestDate', 'validationTestStatus')

    validationTestDate = fields.DateTime(dump_only=True)
    validationTestStatus = fields.String(dump_only=True)


class ConfigurationSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('_links', '_id', 'maxAge', 'syncInterval', 'downloadDelay', 'proxyTestTimeout', 'status')

    #_id = fields.String(data_key='id', dump_only=True)
    maxAge = fields.Integer(required=True, min=1, max=5)
    syncInterval = fields.Integer(required=True, min=1, max=60)
    downloadDelay = fields.Integer(required=True, min=1, max=60)
    proxyTestTimeout = fields.Integer(required=True, min=1, max=10)
    status = fields.Boolean()

    _links = ma.Hyperlinks({
        'self': {
            'href': ma.AbsoluteURLFor('configuration', id='<_id>'),
            'title': 'configuration detail'
        },
        'collection': {
           'href': ma.AbsoluteURLFor('configurationlist'),           
           'title': 'list of configurations'
        }
    })


class ProviderSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('_links', '_id', 'name', 'baseAddress', 'fetcher', 'instructions', 'updateAttempt')

    _id = fields.String(data_key='id', dump_only=True)
    name = fields.String()
    baseAddress = fields.String(required=True, validate=validate.Length(min=10))
    fetcher = fields.String(required=True)
    instructions = fields.String(required=True, validate=validate.Length(min=2))    
    updateAttempt = fields.Dict(keys=fields.Str(), values=fields.Str(), dump_only=True)

    _links = ma.Hyperlinks({
        'self': {
            'href': ma.AbsoluteURLFor('provider', id='<_id>'),
            'title': 'provider detail'
        },
        'collection': {
           'href': ma.AbsoluteURLFor('providerlist'),           
           'title': 'list of providers'
        }
    })


class ProxySchemaBase(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ['_links', '_id', 'providerId', 'ip', 'port', 'funcTestDate', 'lastFoundDate', 'discoveredDate', 'anonymity']

    #_id = fields.String(data_key='id', dump_only=True)
    providerId = util.CustomObjectIdField(required=True)
    ip = fields.String(required=True, validate=validate.Length(min=1))
    port: fields.Integer(required=True)
    lastFoundDate = fields.DateTime(dump_only=True)
    discoveredDate = fields.DateTime(dump_only=True)
    anonymity = fields.String(dump_only=True)
    funcTestDate = fields.DateTime(dump_only=True)

    _links = ma.Hyperlinks({
        'self': {
            'href': ma.AbsoluteURLFor('proxy', id='<_id>'),
            'title': 'proxy detail',
        },
        'collection': {
           'href': ma.AbsoluteURLFor('proxylist'),
           'title': 'list of proxies'
        }
    })


class ProxySchema(ProxySchemaBase):
    _links = ma.Hyperlinks({
        'self': {
            'href': ma.AbsoluteURLFor('proxy', id='<_id>'),
            'title': 'proxy detail',
        },
        'provider': {
            'href': ma.AbsoluteURLFor('provider', id='<providerId>'),
            'title': 'provider detail',
        },
        'collection': {
           'href': ma.AbsoluteURLFor('proxylist'),
           'title': 'list of proxies'
        }
    })

class ProxySchemaEmbedded(ProxySchemaBase):
    class Meta(ProxySchemaBase.Meta):        
        fields = ['_links', 'provider', 'testurls', '_id', 'providerId', 'ip', 'port', 'funcTestDate', 'lastFoundDate', 'discoveredDate', 'anonymity']

    provider = fields.Nested(ProviderSchema, dump_only=True)
    testurls = fields.List(fields.Nested(ProxyTesturlSchema, dump_only=True))
    
    #_embedded = fields.String()
    #@post_dump()
    #def format_embedded(self, data, many, **kwargs):
    #    data['_embedded'] = {'provider': data['provider']}
    #    del data['provider']
    #    return data

class ProviderSchemaEmbedded(ProviderSchema):
    class Meta(ProviderSchema.Meta):
        fields = ('_links', 'proxies', '_id', 'name', 'baseAddress', 'fetcher', 'instructions', 'updateAttempt')

    proxies = fields.List(fields.Nested(ProxySchemaBase, dump_only=True))


class ProviderSchemaCountEmbedded(ProviderSchema):
    class Meta(ProviderSchema.Meta):
        fields = ('_links', 'proxyCount', '_id', 'name', 'baseAddress', 'fetcher', 'instructions', 'updateAttempt')

    proxyCount = fields.Integer(dump_only=True)


class TesturlProxySchema(ProxySchemaBase):
    class Meta(TesturlSchema.Meta):
        fields = ['_links', '_id', 'providerId', 'ip', 'port', 'funcTestDate', 'lastFoundDate', 'discoveredDate', 'anonymity', 'validationTestDate', 'validationTestStatus']

    validationTestDate = fields.DateTime(dump_only=True)
    validationTestStatus = fields.String(dump_only=True)


class TesturlSchemaEmbedded(TesturlSchema):
    class Meta(TesturlSchema.Meta):
        fields = ('_links', 'proxies', '_id', 'url', 'validationAttempt')

    proxies = fields.List(fields.Nested(TesturlProxySchema, dump_only=True))

# endregion


# region webargs_schemas

params_schema = {
    "limit": webargs.fields.Int(missing=sys.maxsize, validate=lambda x: x >= 0),
    "offset": webargs.fields.Int(missing=0, validate=lambda x: x >= 0),
    "embed": webargs.fields.Boolean(missing=False),
    "anonymities": webargs.fields.String(),
    "providers": webargs.fields.String(),
    "syncTest": webargs.fields.Integer(missing=0, validate=lambda x: x in [0, 1, 2]),
    "validate": webargs.fields.Bool(missing=False),
    "sort": webargs.fields.String(),
    "order": webargs.fields.String()
}

# endregion