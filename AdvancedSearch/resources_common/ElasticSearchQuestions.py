from flask import jsonify
from flask_restful import Resource, Api, reqparse,request
from elasticsearch import Elasticsearch
import os
import glob
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk import sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import string
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

class ElasticSearchQuestions(Resource):
    def get(self):
        es=Elasticsearch()
        result = es.search(index=config.get('word_indexing','q_index_word'),size=100)['hits']['hits']
        unique_questions=[]
        print('Check Indexed Questions:',result)
        for row in result:
            unique_questions.append(row['_id'].replace('+',' '))

        return {"q":unique_questions}
