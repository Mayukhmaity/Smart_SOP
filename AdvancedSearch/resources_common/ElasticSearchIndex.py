#!/usr/bin/env python
# coding: utf-8


from elasticsearch import Elasticsearch
from flask_restful import Resource
from flask import jsonify, request
import os
import glob
import configparser
import datetime
from nltk.tokenize import word_tokenize
from resources_common.WordPdfExtraction import WordPdfExtraction
#from apscheduler.scheduler import Scheduler
from Model import DocumentSchema

config = configparser.ConfigParser()
config.read('config.ini')


class ElasticSearchIndex(Resource):
    #Index data into elasticsearch index: cricket_stadiums

    def postCustom(self):
        #try:
        es=Elasticsearch()
        wpe=WordPdfExtraction()
        filename=config.get('indexing','filename')
        filename_doc=config.get('word_indexing','filename_doc')
        df=None
        df_docx=None
        os.chdir(filename)
        files=glob.glob("*.*")
        df=wpe.extractPdf(files)
        os.chdir(os.path.dirname(__file__))

        os.chdir(filename_doc)
        files_doc=glob.glob("*.*")
        df_docx=wpe.extractWord(files_doc)


        colnums=df.columns
        colnums_doc = df_docx.columns
       # print('PDF',colnums)
       # print('WORD',colnums_doc)
        counter=1
        new_counter = 1
        #print('df is:',df)

        if not df.empty:
            for row_number in range(df.shape[0]):
                body = dict([(name, str(df.iloc[row_number][name])) for name in colnums])
                resp = es.index(id=counter, index=config.get('indexing', 'index'),body=body)
                #print('done', config.get('indexing', 'index'), resp)
                counter += 1

        if not df_docx.empty:
            # for row_number in range(df.shape[0]):
            #     body=dict([(name,str(df.iloc[row_number][name])) for name in colnums ])
            #     resp=es.index(id=counter, index=config.get('indexing','index'),body=body)
            #     print('done',config.get('indexing','index'),resp)
            #     new_counter+=1
            for row_number in range(df_docx.shape[0]):
                body_doc = dict([(name,str(df_docx.iloc[row_number][name])) for name in colnums_doc ])
                resp_doc=es.index(id=new_counter, index=config.get('word_indexing','index_word'),body=body_doc)
                #print('done', config.get('word_indexing', 'index_word'), resp_doc)
                new_counter += 1

            print("Indexing successful document and pdf")
        else:
            print("Documents are already up-to-date")

        return 1

        '''except Exception as e:
            output= "Something bad happenned. Please try Again."
        finally:
            return output'''

