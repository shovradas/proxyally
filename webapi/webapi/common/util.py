
from marshmallow import fields, post_dump, ValidationError
from flask_restful import abort
from bson.objectid import ObjectId

def var_dump(data):
    print('\n\n##############################\n', data, '\n##############################\n\n')


def abort_if_doesnt_exist(result, **kwargs):    
    if result is None or not result:
        abort(404, message="Resource doesn't exist", status="error", **kwargs)


def abort_if_invalid_id_format(id, **kwargs):
    try:
        id = ObjectId(id)
    except:
        abort(422, message="Invalid ID supplied", status="error", **kwargs)


class CustomObjectIdField(fields.Field):
    """Field that serializes to a string of numbers and deserializes
    to a list of numbers.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        try:
            id = ObjectId(value)
            return str(value)
        except ValueError as error:
            raise ValidationError("Invalid format") from error

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return ObjectId(value)
        except ValueError as error:
            raise ValidationError("Invalid format") from error