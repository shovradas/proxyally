
from flask import url_for
from flask_restful import Resource
from webargs.flaskparser import use_args
from marshmallow import fields, post_dump
from bson.objectid import ObjectId
from webapi import api, mongo
from webapi.common import util
from webapi.schemas import UserSchema, params_schema, LoginSchema
import hashlib, datetime


user_schema = UserSchema()
users_schema = UserSchema(many=True)

login_schema = LoginSchema()



@api.resource('/api/v1/users/<id>')
class User(Resource):
    def get(self, id):
        util.abort_if_invalid_id_format(id)
        doc = mongo.db.users.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)
        return user_schema.dump(doc)
    
    def delete(self, id):
        util.abort_if_invalid_id_format(id)
        mongo.db.users.delete_one({ '_id': ObjectId(id) })
        return '', 204

    @use_args(user_schema, location='json_or_form')
    def put(self, args, id):
        util.abort_if_invalid_id_format(id)
        args['lastUpdatedDate'] = datetime.datetime.now()
        doc = mongo.db.users.find_one({'_id': ObjectId(id)})
        util.abort_if_doesnt_exist(doc)   
        mongo.db.users.update_one({ '_id': ObjectId(id) }, { '$set': args })
        return '', 204


@api.resource('/api/v1/users')
class UserList(Resource):
    @use_args(params_schema, location="query")
    def get(self, args):
        docs = mongo.db.users.find().skip(args['offset']).limit(args['limit'])   
        return users_schema.dump(docs)

    @use_args(user_schema, location='json_or_form')
    def post(self, args):
        args['password'] = hashlib.md5(args['password'].encode()).hexdigest()
        args['createddDate'] = datetime.datetime.now()
        args['lastUpdatedDate'] = datetime.datetime.now()
        result = mongo.db.users.insert_one(args)
        doc = mongo.db.users.find_one({'_id': result.inserted_id})
        return user_schema.dump(doc), 201, {'location': url_for('user', id=f'{result.inserted_id}')}


#@api.resource('/api/v1/users/login')
#class UserLogin(Resource):
#    @use_args(login_schema, location='headers')
#    def post(self, args):
#        return args
#        args['password'] = hashlib.md5(args['password'].encode()).hexdigest()
#        user = mongo.db.users.find_one({'email', args['email']})
#        if(user['password']==args['password']):       
#            return login_schema.dump(user)
#        else:
#            return 500