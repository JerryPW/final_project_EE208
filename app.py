# SJTU EE208
INDEX_DIR = "IndexFiles.index"

import Levenshtein   #计算相似度
import re
import sys, os, lucene,jieba
from java.io import File
from java.nio.file import Path
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import SimpleAnalyzer ,WhitespaceAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.util import Version
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import BooleanClause
from org.apache.lucene.search.highlight import Highlighter, QueryScorer, SimpleFragmenter, SimpleHTMLFormatter
from typing import KeysView
from flask import Flask, redirect, render_template, request, url_for
import urllib.error
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
title = ''
url = ''
date = ''
app = Flask(__name__,static_url_path='/static')

##关键词搜索
def search(keyword):
    STORE_DIR = "163_index"
    vm.attachCurrentThread()
    directory=SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher=IndexSearcher(DirectoryReader.open(directory))
    analyzer=StandardAnalyzer()

    res_cnt,res_list=get_res(searcher,analyzer,keyword)
    return res_cnt,res_list

#返回关键词搜索结果#
def get_res(searcher,analyzer,keyword):
    command_dict = parseCommand(keyword)
    querys = BooleanQuery.Builder()
    for k,v in command_dict.items():
        query = QueryParser(k, analyzer).parse(v)
        querys.add(query, BooleanClause.Occur.MUST)
    query=QueryParser("contents",analyzer).parse(keyword)
    scoreDocs=searcher.search(query, 50).scoreDocs
    res_list=[]
    for i, scoreDoc in enumerate(scoreDocs):
        doc = searcher.doc(scoreDoc.doc)
        res={}
        res['title']=doc.get('title')
        res['url']=doc.get('url')
        res['date']=doc.get('date')
        res['contents'] = urllib.request.urlopen(doc.get('url'))
        res_list.append(res)
    res_list = simility(res_list)
    return len(scoreDocs),res_list

#按时间排序
def search_by_time(keyword):
    res_cnt,res_list=search(keyword)
    for i in range(len(res_list)):
        for j in range(len(res_list)-1-i):
            if timeCompare(res_list[j]['date'], res_list[j+1]['date']) == 0:
                res_list[j]['title'], res_list[j+1]['title'] = res_list[j+1]['title'], res_list[j]['title']
                res_list[j]['date'], res_list[j+1]['date'] = res_list[j+1]['date'], res_list[j]['date']
                res_list[j]['url'], res_list[j+1]['url'] = res_list[j+1]['url'], res_list[j]['url']
                res_list[j]['contents'], res_list[j+1]['contents'] = res_list[j+1]['contents'], res_list[j]['contents']
    return res_cnt, res_list

def parseCommand(command):
    command_dict = {'contents': ''}   
    command_dict['contents'] = ' '.join(jieba.cut(command))
    return command_dict

def timeCompare(time1, time2): # 1 -> time1 >= time2; 0 -> times2 > time1
    time1 = time1.split('-')
    time2 = time2.split('-')
    for i in range(len(time1)):
        if int(time1[i]) > int(time2[i]):
            return 1
        elif int(time1[i]) < int(time2[i]):
            return 0
        else:
            continue
    return 1

#相似度
def simility(res_list):
    simility = []
    length = len(res_list)
    length1 = length
    pos = 1
    while(pos < length1):
        length = length1
        while(length > pos):
            simility.append(Levenshtein.ratio(res_list[pos - 1]['title'],res_list[length - 1]['title']))
            length -= 1
        length = length1
        while(length > pos):
            maxq = simility.index(max(simility))
            if(simility[maxq] >= 0.4):
                simility[maxq] = 0
                res_list[pos]['title'], res_list[maxq]['title'] = res_list[maxq]['title'], res_list[pos]['title']
                res_list[pos]['date'], res_list[maxq]['date'] = res_list[maxq]['date'], res_list[pos]['date']
                res_list[pos]['url'], res_list[maxq]['url'] = res_list[maxq]['url'], res_list[pos]['url']
                res_list[pos]['contents'], res_list[maxq]['contents'] = res_list[maxq]['contents'], res_list[pos]['contents']
                pos += 1
            else:
                break
            length -= 1
        pos += 1
    return res_list

@app.route('/')
def form_1():
    return render_template("index.html")

@app.route('/t')
def form_t():
    return render_template("test.html")

@app.route('/word')
def form_2():
    return render_template("word.html")

@app.route('/img')
def form_3():
    return render_template("img.html")

@app.route('/face')
def form_4():
    return render_template("face.html")

@app.route('/wdresult', methods=['GET','POST'])
def wd_result():
    keyword=request.args.get('keyword')
    res_cnt,res_list=search(keyword)
    res_cnt_1,res_list_1=search_by_time(keyword)
    return render_template("result.html", keyword=keyword,res_cnt=res_cnt,res_list=res_list,res_cnt_1=res_cnt_1,res_list_1=res_list_1)

if __name__ == '__main__':
    last_search = ''

    try:
        vm = lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    except:
        vm = lucene.getVMEnv()

    app.run(debug=True,port = 8081)
    
    