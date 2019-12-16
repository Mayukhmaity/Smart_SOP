import nltk
import numpy as np
import random
import string # to process standard python strings
from docx import Document
from elasticsearch import Elasticsearch
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet as wn
from textblob.en import sentiment as pattern_sentiment
from flask_restful import Resource, Api, reqparse,request
from flask import jsonify
from scipy.spatial.distance import pdist
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

lemmer = nltk.stem.WordNetLemmatizer()
stm = PorterStemmer()
wnl = WordNetLemmatizer()
doc = Document(r'C:\Users\mayukhm505\Documents\Document\Draft HZL O2C SOP (Metal Sales).docx')
raw = ''
for para in doc.paragraphs:
    raw += ' ' + para.text

class SearchQueryOptimize(Resource):

# WordNet is a semantically-oriented dictionary of English included in NLTK.
        def LemTokens(self,tokens):
            return [lemmer.lemmatize(token) for token in tokens]


        def LemNormalize(self,text):
            remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
            return self.LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))


# Custom distance function
        def distance_between(self,x, y):
            return abs(x - y)


        def matched_positions_minimum_distance(self,filtered_tokens):
            all_matched_pos = []
            pos_dict = {}
            for name, pos in filtered_tokens:
                for p in pos:
                    exact_word_pos = p
                    if name not in pos_dict.keys():
                        pos_dict[name] = exact_word_pos
                        all_matched_pos.append(exact_word_pos)
                    else:
                        previous_pos = pos_dict[name]
                        dist_is_lesser = True
                        for key, value in pos_dict.items():
                            if key != name:
                                if (self.distance_between(exact_word_pos, value) > self.distance_between(previous_pos, value)):
                                    dist_is_lesser = False
                                    break
                        if dist_is_lesser == True:
                            all_matched_pos.remove(previous_pos)
                            pos_dict[name] = exact_word_pos
                            all_matched_pos.append(exact_word_pos)
            return all_matched_pos


        def all_pos(self,matcher, sent):
            pos_array = []
            matcher_tokens = self.MyLemmaTokenizer(matcher)
            sent_tokens = self.MyLemmaTokenizer(sent)
            for each_token in matcher_tokens:
                sent_pos = 0
                pos = []
                for each_sent_token in sent_tokens:
                    if each_token == each_sent_token:
                        pos.append(sent_pos)
                    sent_pos += 1
                pos_array.append((each_token, pos))
            return pos_array


        def minimum_traverse_distance(self,matcher, sentence):
            positions = self.matched_positions_minimum_distance(self.all_pos(matcher, sentence))
            if len(positions) == 0:
                return 0
            positions.sort()
            dist = 0
            prev = positions[0]
            for next in positions[1:]:
                dist += (abs(prev - next))
                prev = next
            return dist


        def MyLemmaTokenizer(self,text):
            stop_words = set(stopwords.words("english"))
            puncs = ['?', '!', '.', ';', ',', '$', '@', '&', '#', '%', '*', ':', ':)', ':(', ':P', ':D', ':-)', ':-(', '(', ')',
             '\'s', '-', '/']
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
                                word = stm.stem(word)
                                word = wnl.lemmatize(word)
                                tokens.append(word)
            return tokens


        def response(self,user_response):
            sent_tokens = nltk.sent_tokenize(raw)  # converts to list of sentences
            word_tokens = nltk.word_tokenize(raw)  # converts to list of words
            robo_response = ''
            sent_tokens.append(user_response)
            TfidfVec = TfidfVectorizer(tokenizer=self.MyLemmaTokenizer, stop_words='english')
            tfidf = TfidfVec.fit_transform(sent_tokens)
            vals = cosine_similarity(tfidf[-1], tfidf)
            idx_array = vals.argsort()[0][-2:-1]
            idx_array = idx_array[::-1]
            flat = vals.flatten()
            flat.sort()
            req_tfidf = flat[-2]
            if (req_tfidf == 0):
                robo_response = robo_response + "I am sorry! I don't understand you"
                sent_tokens.remove(user_response)
                return robo_response
            else:
                distance_min = 9999999
                answer_idx = None
                for idx in idx_array:
                    distance = self.minimum_traverse_distance(user_response, sent_tokens[idx])
                    # print(distance)
                    if distance != 0 and distance < distance_min:
                        answer_idx = idx
                        distance_min = distance
                robo_response = robo_response + sent_tokens[answer_idx]
                sent_tokens.remove(user_response)
                return robo_response
        def get(self):
            keyword = request.args.get('keyword', '')
            matched_sentence_doc = self.response(keyword)
            break_matched_sentence_doc = word_tokenize(matched_sentence_doc)
            link = break_matched_sentence_doc[0]+' '+break_matched_sentence_doc[1]+' '+break_matched_sentence_doc[2]
            output = {"result": {"answer": matched_sentence_doc,"link":link, "available":True}}

            # Finally index questions  for cached mechanism
            es = Elasticsearch()
            body = {"data": ""}
            op = es.index(index=config.get('word_indexing', 'q_index_word'), id=keyword.lower(), body=body)
            print(op)
            return (jsonify(output))


