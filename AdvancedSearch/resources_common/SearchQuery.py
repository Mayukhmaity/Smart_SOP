import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from flask_restful import Resource, Api, reqparse,request
from nltk.stem import PorterStemmer
from flask import jsonify
from elasticsearch import Elasticsearch
import numpy as np
import logging
from docx import Document
from nltk.tokenize import sent_tokenize
from scipy.spatial.distance import cosine
from nltk import word_tokenize, pos_tag
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

class SearchQuery(Resource):
    # def word_averaging(self, wv, words):
    #     all_words, mean = set(), []
    #
    #     for word in words:
    #         if isinstance(word, np.ndarray):
    #             mean.append(word)
    #         elif word in wv.vocab:
    #             # print(word)
    #             mean.append(wv.syn0norm[wv.vocab[word].index])
    #             all_words.add(wv.vocab[word].index)
    #
    #     if not mean:
    #         logging.warning("cannot compute similarity with no input %s", words)
    #         # FIXME: remove these examples in pre-processing
    #         return np.zeros(wv.vector_size, )
    #
    #     mean = gensim.matutils.unitvec(np.array(mean).mean(axis=0)).astype(np.float32)
    #     return mean
    #
    # def word_averaging_list(self, wv, text_list):
    #     return np.vstack([self.word_averaging(wv, post) for post in text_list])

    def w2v_tokenize_text(self,text):
        ps = PorterStemmer()
        lemma = WordNetLemmatizer()
        stop_words = set(stopwords.words("english"))
        puncs = ['sop', 'are', 'is', 'will', 'shall', '?', '!', '.', ';', ',', '$', '@', '&', '#', '%', '*', ':', ':)',
                 ':(', ':P', ':D', ':-)', ':-(', '(', ')', '\'s', '-', '/']
        tokens = []
        for sent in nltk.sent_tokenize(text, language='english'):

            for word in nltk.word_tokenize(sent, language='english'):
                '''if len(word) < 2:
                    continue'''
                word = word.lower()
                if word not in stop_words and word not in puncs:
                    # if not any(ch.isdigit() for ch in word):
                    isalpha = 1
                    for ch in word:
                        if not ch.isalpha():
                            isalpha = 0
                    if isalpha == 1:
                        word = ps.stem(word)
                        word = lemma.lemmatize(word)
                        tokens.append(word)
        return tokens

    def get_all_words(self,doc_new,all_words):
        for sent in doc_new:
            for w in sent:
                all_words.append(w.lower())
        return all_words


    def find_features(self, words_in_a_document, all_words):
        words = set(words_in_a_document)
        features = []
        for w in all_words:
            flag = 0
            if w in words:
                flag = 1
            features.append(flag)
        return features

    def get(self):
        doc = Document(r'C:\Users\mayukhm505\Documents\Document\Draft HZL O2C SOP (Metal Sales).docx')
        keyword = request.args.get('keyword', '')
        doc_new = []
        sentences = []
        all_words = []

        for para in doc.paragraphs:
            sen = sent_tokenize(para.text)
            for s in sen:
                sentences.append(s)
                words = self.w2v_tokenize_text(s)
                doc_new.append(words)
        for sent in doc_new:
            for w in sent:
                all_words.append(w.lower())
        cosines = []
        v_test = self.find_features(self.w2v_tokenize_text(keyword),all_words)
        index = 0
        for sen in doc_new:
            v_train = self.find_features(sen,all_words)
            cosines.append(((1 - cosine(v_train, v_test)), index))
            index += 1

        cosines.sort(reverse=True)
        matched_sentence_doc = sentences[cosines[0][1]]
        break_matched_sentence_doc = word_tokenize(matched_sentence_doc)
        link = break_matched_sentence_doc[0] + ' ' + break_matched_sentence_doc[1] + ' ' + break_matched_sentence_doc[2]
        output = {"result": {"answer": matched_sentence_doc,"link":link,"available":True}}
        es = Elasticsearch()
        body = {"data": ""}
        op = es.index(index=config.get('word_indexing', 'q_index_word'), id=keyword.lower(), body=body)
        print(op)
        return jsonify(output)




