from flask import Blueprint, request, url_for, json
from flask_restful import Api
from resources_common.ElasticSearchQuery import ElasticSearchQuery
from resources_common.ElasticSearchIndex import ElasticSearchIndex
from resources_common.ElasticSearchQuestions import ElasticSearchQuestions
from resources_common.SearchQuery import SearchQuery
from resources_common.SearchQueryOptimize import SearchQueryOptimize
from flask import Flask, render_template, send_file, send_from_directory
import os

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Route
api.add_resource(SearchQueryOptimize, '/doQuery')
api.add_resource(ElasticSearchIndex, '/doIndex')
api.add_resource(ElasticSearchQuestions,'/getQuestions')

#Views Route
@api_bp.route('/home')
def homepage():
    image = 'pwc.jpg'
    return render_template('homepage.html', user_image = image)
@api_bp.route('/doc')
def doc():
    return render_template('doc.html')
@api_bp.route('/homepage')
def home():
    return render_template('homepage_revise.html')
@api_bp.route('/frame')
def frame():
    return render_template('frames.html')

@api_bp.route('/show')
def show_static_pdf():
    return send_from_directory('data',request.args.get('path',type = str))

# @api_bp.route('/particle')
# def showjson():
#     SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
#     json_url = os.path.join(SITE_ROOT, "static/data", "particles.json")
#     data = json.load(open(json_url))
#     return render_template('showjson.jade', data=data)
