
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
        fields = ('_links', '_id', 'url', 'description')

    _id = util.CustomObjectIdField(data_key='id', dump_only=True)
    url = fields.String(required=True, validate=validate.Length(min=1))
    description = fields.String(required=True)

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
        fields = ('_links', '_id', 'url', 'description', 'urlFuncTestDate')

    urlFuncTestDate = fields.DateTime(required=True)


class ConfigurationSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('_links', '_id', 'maxAge', 'syncInterval', 'downloadDelay', 'proxyTestTimeout', 'status')

    #_id = fields.String(data_key='id', dump_only=True)
    maxAge = fields.Integer(required=True, min=1, max=5)
    syncInterval = fields.Integer(required=True, min=10, max=60)
    downloadDelay = fields.Integer(required=True, min=1, max=60)
    proxyTestTimeout = fields.Integer(required=True, min=1, max=30)
    status = fields.Boolean(required=True)

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


class LoginSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('email', 'password')
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, validate=validate.Length(min=8, max=255), load_only=True)


class UserSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('_links', '_id', 'email', 'password', 'pin')

    _id = fields.String(data_key='id', dump_only=True)
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, validate=validate.Length(min=8, max=255), load_only=True)
    pin = fields.Integer(required=True, load_only=True)
    createdDate = fields.Date(dump_only=True)
    lastUpdatedDate = fields.Date(dump_only=True)

    _links = ma.Hyperlinks({
        'self': {
            'href': ma.AbsoluteURLFor('user', id='<_id>'),
            'title': 'user detail'
        },
        'collection': {
           'href': ma.AbsoluteURLFor('userlist'),           
           'title': 'list of users'
        }
    })


class ProviderSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        fields = ('_links', '_id', 'name', 'baseAddress', 'fetcher', 'instructions', 'updateAttempt')

    _id = fields.String(data_key='id', dump_only=True)
    name = fields.String()
    baseAddress = fields.String(required=True, validate=validate.Length(min=10))
    fetcher = fields.String()
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
    funcTestDate = fields.DateTime(dump_only=True)
    lastFoundDate = fields.DateTime(dump_only=True)
    discoveredDate = fields.DateTime(dump_only=True)
    anonymity = fields.String(required=True, validate=validate.Length(min=1))

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


class TesturlProxySchema(ProxySchemaBase):
    class Meta(TesturlSchema.Meta):
        fields = ['_links', '_id', 'providerId', 'ip', 'port', 'funcTestDate', 'lastFoundDate', 'discoveredDate', 'anonymity', 'urlFuncTestDate']

    urlFuncTestDate = fields.DateTime(required=True)


class TesturlSchemaEmbedded(TesturlSchema):
    class Meta(TesturlSchema.Meta):
        fields = ('_links', 'proxies', '_id', 'url', 'description')

    proxies = fields.List(fields.Nested(TesturlProxySchema, dump_only=True))

# endregion


# region webargs_schemas

params_schema = {
    "limit": webargs.fields.Int(missing=25, validate=lambda x: x >= 0),
    "offset": webargs.fields.Int(missing=0, validate=lambda x: x >= 0),
    "embed": webargs.fields.Boolean(missing=False),
    "anonymities": webargs.fields.String(),
    "providers": webargs.fields.String(),
    "syncTest": webargs.fields.Integer(missing=0, validate=lambda x: x in [1, 2])
}

# endregion