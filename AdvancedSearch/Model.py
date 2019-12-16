from flask import Flask
from marshmallow import Schema, fields, pre_load, validate
from flask_marshmallow import Marshmallow

ma = Marshmallow()

class DocumentSchema(ma.Schema):
    index = fields.String(required=True)
    filename = fields.String(required=True)

class Position:
    name = fields.String(required=True)
    paragraph=fields.Integer(required=True)
    statistics=fields.String(required=True)

class SearchResultSchema(ma.Schema):
    highlighted = fields.String(required=True)