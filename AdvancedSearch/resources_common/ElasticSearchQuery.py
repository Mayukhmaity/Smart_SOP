#!/usr/bin/env python
# coding: utf-8

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
import textract
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

class ElasticSearchQuery(Resource):

    config=configparser.ConfigParser()

    def get_content(self,keyword,index):
        es = Elasticsearch()
        body={'_source':["name","page","para","content"],'query':{'match_phrase_prefix':{"content":{"query":keyword}}}}
        print(index)
        result=es.search(index=index,body=body)['hits']['hits']

        result_contents=[]
        for row in result:
            result_contents.append(row['_source'])
        return result_contents

    def get_content_doc(self, keyword, index):
        es = Elasticsearch()
        body_doc = {'_source_doc': ["name", "paragraph", "content"],
                'query': {'match_phrase_prefix': {"content": {"query": keyword}}}}
        print(index)
        result = es.search(index=index, body=body_doc)['hits']['hits']

        result_contents = []
        for row in result:
            result_contents.append(row['_source_doc'])
        return result_contents

    def get(self):
        #try:
        keyword=request.args.get('keyword', '')
        index=config.get('indexing','index')
        if not keyword:
            return "One or More parameter is incorrect"
        clean_words=[]
        tokenizer = RegexpTokenizer(r'\w+')
        tokenized=tokenizer.tokenize(keyword)
        stop_words=set(stopwords.words('english'))
        for each_word in tokenized:
            if each_word not in stop_words and each_word not in string.punctuation:
                clean_words.append(each_word)
        positions={}
        tokens=[]
        text=[]
        initial_match = []
        for each_clean_word in clean_words:
            self_position=self.get_position(each_clean_word,index)

            positions[each_clean_word]=self_position
            for pos in self_position:
                pos_tokens=pos['positioning']['tokens']
                #print(pos)
                tokens.append((each_clean_word, pos['filename'], pos['page'], pos['para'],pos_tokens, pos['text']))
                initial_match.append({each_clean_word: {"file": pos['filename'], "page_no": pos['page'],
                                                        "para_no": pos['para'],"positioning": pos_tokens, "paragraph": pos['text']}})
                text.append(pos['text'])

            #print("Text is", text)
            #print(tokens)
        new_text = text[1:]
        if tokens==[] or new_text==[]:
            return "No Match Found. Please refine your Query"
        most_common_text, num_most_common_text = Counter(new_text).most_common(1)[0]
        most_common_text_doc, num_most_common_text_doc = Counter(new_text).most_common(1)[0]

        print("Common Text",most_common_text)
        print("Number of common text", num_most_common_text)

        filtered_tokens = [t for t in tokens if t[5] == most_common_text]
        filtered_tokens_doc = [t for t in tokens if t[5] == most_common_text_doc]

        final_para=''
        final_filename=''
        if filtered_tokens != []:
            final_para=filtered_tokens[0][5]
            final_page=filtered_tokens[0][2]
            final_filename=filtered_tokens[0][1]
        else:
            return "No Match Found. Please refine your Query"

        sentences=sent_tokenize(final_para)

        sent_list=[]
        pos_first_word=1
        for sen in sentences:
            tokenizer = RegexpTokenizer(r'\w+')
            word_token_para = tokenizer.tokenize(sen)
            sent_list.append((pos_first_word, pos_first_word+len(word_token_para), sen))
            pos_first_word=pos_first_word+len(word_token_para)+1



        matched_sentence="No Result found. Please tune your query further."
        target=[]
        for pos in self.matched_positions_minimum_distance(filtered_tokens):
            for first_word_pos, last_word_pos, sent in sent_list:
                if pos <=last_word_pos and pos >=first_word_pos:
                    target.append(sent)

        matched_sentence,freq=Counter(target).most_common(1)[0]
        matched_sentence_doc = self.get_doc(keyword)
        final_page_new = int(final_page)+1
        print(final_page)
        created_link=final_filename+"#page="+str(final_page_new)
        output= {"result":{"answer":matched_sentence_doc,"link":created_link}}

        #Finally index questions  for cached mechanism
        es=Elasticsearch()
        body={"data":""}
        es.index(index=config.get('indexing', 'q_index'), id=keyword.lower(), body=body)

        return(jsonify(output))
        '''except Exception as e:
            return "Exception Occurred, ",str(e)'''

    def matched_positions_minimum_distance(self,filtered_tokens):
        all_matched_pos = []
        pos_dict = {}
        for name, file,page, para, pos, text in filtered_tokens:
            for p in pos:
                exact_word_pos = p['position']
                print('exact words', exact_word_pos)
                if name not in pos_dict.keys():
                    pos_dict[name] = exact_word_pos
                    all_matched_pos.append(exact_word_pos)
                else:
                    previous_pos = pos_dict[name]
                    dist_is_lesser=True
                    for key, value in pos_dict.items():
                        if key != name:
                            if (self.distance_between(exact_word_pos, value) > self.distance_between(previous_pos, value)):
                                dist_is_lesser=False
                                break
                    if dist_is_lesser ==True:
                        all_matched_pos.remove(previous_pos)
                        pos_dict[name] = exact_word_pos
                        all_matched_pos.append(exact_word_pos)
        return all_matched_pos

    def matched_positions_minimum_distance_doc(self, filtered_tokens):
        all_matched_pos = []
        pos_dict = {}
        for name, file, pos, text in filtered_tokens:
            for p in pos:
                exact_word_pos = p['position']
                print('exact words', exact_word_pos)
                if name not in pos_dict.keys():
                    pos_dict[name] = exact_word_pos
                    all_matched_pos.append(exact_word_pos)
                else:
                    previous_pos = pos_dict[name]
                    dist_is_lesser = True
                    for key, value in pos_dict.items():
                        if key != name:
                            if (self.distance_between(exact_word_pos, value) > self.distance_between(previous_pos,
                                                                                                     value)):
                                dist_is_lesser = False
                                break
                    if dist_is_lesser == True:
                        all_matched_pos.remove(previous_pos)
                        pos_dict[name] = exact_word_pos
                        all_matched_pos.append(exact_word_pos)
        return all_matched_pos

    def distance_between(self,x,y):
        if x<y:
            return y-x
        else:
            return x-y

    def get_position(self,keyword,index):
        output=[]
        highlighted_text=self.get_keyword_highlighted(keyword,index)
        es = Elasticsearch()
        tokenized_phrase=word_tokenize(keyword)
        result_content=self.get_content(keyword,index)
        contentIter=0
        for each_content in result_content:
            body={
                    "doc": {
                          "content": each_content['content']
                    },
                    "offsets" : 'true',
                    "payloads" : 'true',
                    "positions" : 'true',
                    "term_statistics" : 'true',
                    "field_statistics" : 'true',
                    "fields": ["content"]
            }

            term_statistics=es.termvectors(index=index, body=body)
            all_terms=term_statistics['term_vectors']['content']['terms']
            keys=all_terms.keys()
            for each_phrase in tokenized_phrase:
                for term in keys:
                    if term==each_phrase:
                        mydict={"term":term,"filename":each_content['name'],
                                "page":each_content['page'],
                                "para":each_content['para'],
                                "positioning":all_terms[term],
                                "text":each_content['content']}
                        #mytuple=(term,each_content['name'],each_content['paragraph'],all_terms[term],highlighted_text[contentIter])
                        output.append(mydict)
                        contentIter+=1
        return output

    def get_position_doc(self,keyword,index):
        output=[]
        highlighted_text=self.get_keyword_highlighted(keyword,index)
        es = Elasticsearch()
        tokenized_phrase=word_tokenize(keyword)
        result_content=self.get_content(keyword,index)
        contentIter=0
        for each_content in result_content:
            body={
                    "doc": {
                          "content": each_content['content']
                    },
                    "offsets" : 'true',
                    "payloads" : 'true',
                    "positions" : 'true',
                    "term_statistics" : 'true',
                    "field_statistics" : 'true',
                    "fields": ["content"]
            }

            term_statistics=es.termvectors(index=index, body=body)
            all_terms=term_statistics['term_vectors']['content']['terms']
            keys=all_terms.keys()
            for each_phrase in tokenized_phrase:
                for term in keys:
                    if term==each_phrase:
                        mydict={"term":term,"filename":each_content['name'],
                                #"para":each_content['para'],
                                "positioning":all_terms[term],
                                "text":each_content['content']}
                        #mytuple=(term,each_content['name'],each_content['paragraph'],all_terms[term],highlighted_text[contentIter])
                        output.append(mydict)
                        contentIter+=1
        return output


    def get_keyword_highlighted(self,keyword,index):
        es = Elasticsearch()
        highlights=[]
        body={
              "query": {
                "match_phrase": {
                  "content": {
                    "query": keyword
                    , "analyzer": "stop"
                  }
                }
              },
              "highlight": {
                "fields": {
                  "content": {"number_of_fragments": 0}
                }
              }
            }
        result=es.search(index=index,body=body)['hits']['hits']
        for each_result in result:
            highlights.append(each_result['highlight']['content'])
        return highlights

    def get_doc(self,keyword):
        # try:
      #  keyword = request.args.get('keyword', '')
        index = config.get('word_indexing', 'index_word')
        if not keyword:
            return "One or More parameter is incorrect"
        clean_words = []
        tokenizer = RegexpTokenizer(r'\w+')
        tokenized = tokenizer.tokenize(keyword)
        stop_words = set(stopwords.words('english'))
        for each_word in tokenized:
            if each_word not in stop_words and each_word not in string.punctuation:
                clean_words.append(each_word)
        positions_doc = {}
        tokens_doc = []
        text_doc = []
        initial_match_doc = []
        for each_clean_word in clean_words:
            self_position = self.get_position_doc(each_clean_word, index)

            positions_doc[each_clean_word] = self_position
            for pos in self_position:
                pos_tokens_doc = pos['positioning']['tokens']
                # print(pos)
                tokens_doc.append((each_clean_word, pos['filename'], pos_tokens_doc, pos['text']))
                initial_match_doc.append({each_clean_word: {"file": pos['filename'],"positioning": pos_tokens_doc,
                                                        "paragraph": pos['text']}})
                text_doc.append(pos['text'])

            print("Text Doc is ", text_doc)
            # print(tokens)
        new_text = text_doc[1:]
        if tokens_doc == [] or new_text == []:
            return "No Match Found. Please refine your Query"
        most_common_text_doc, num_most_common_text_doc = Counter(new_text).most_common(1)[0]

        print("Common Text in Doc", most_common_text_doc)
        print("Number of common text in Doc", num_most_common_text_doc)

        filtered_tokens_doc = [t for t in tokens_doc if t[3] == most_common_text_doc]
        print('Word filtered token', filtered_tokens_doc)

        final_para = ''
        final_filename = ''
        if filtered_tokens_doc != []:
            final_para = filtered_tokens_doc[0][3]
           # final_page = filtered_tokens_doc[0][2]
            final_filename = filtered_tokens_doc[0][1]
        else:
            return "No Match Found. Please refine your Query"

        print('Final Para Word', final_para)
        sentences = sent_tokenize(final_para)

        print('Tokenized Sentence word', sentences)

        sent_list = []
        pos_first_word = 1
        for sen in [final_para]:
            tokenizer = RegexpTokenizer(r'\w+')
            word_token_para = tokenizer.tokenize(sen)
            sent_list.append((pos_first_word, pos_first_word + len(word_token_para), sen))
            pos_first_word = pos_first_word + len(word_token_para) + 1

        print('Sent List Word: ',sent_list)
        matched_sentence = "No Result found. Please tune your query further."
        target = []
        for pos in self.matched_positions_minimum_distance_doc(filtered_tokens_doc):
            for first_word_pos, last_word_pos, sent in sent_list:
                if pos <= last_word_pos and pos >= first_word_pos:
                    target.append(sent)
        print('Target', target)
        matched_sentence = Counter(target).most_common(1)
        print('Match Sentence for Word Document', matched_sentence)
        #print(final_page)
        #created_link = final_filename + "#page=" + final_page
        #output = {"result": {"answer": matched_sentence, "link": created_link}}

        # Finally index questions  for cached mechanism
        es = Elasticsearch()
        body = {"data": ""}
        es.index(index=config.get('word_indexing', 'q_index_word'), id=keyword.lower(), body=body)

        return matched_sentence
        '''except Exception as e:
            return "Exception Occurred, ",str(e)'''






