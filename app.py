# SJTU EE208
INDEX_DIR = "IndexFiles.index"

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
tt = ''
tll = []
uu = []
con = []
time = []

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


def runs(searcher, analyzer,command, mode):
    global title,url,tt
    global tll,uu,con,time
    tll = []
    uu = []
    con = []
    time = []
    while True:
        print()
        print ("Hit enter with no input to quit.")        
        if command == '':
            return
        print()
        print ("Searching for:", command)
        command_dict = parseCommand(command)
        querys = BooleanQuery.Builder()
        for k,v in command_dict.items():
            query = QueryParser(k, analyzer).parse(v)
            querys.add(query, BooleanClause.Occur.MUST)
        scoreDocs = searcher.search(querys.build(), 50).scoreDocs
        print("%s total matching documents." % len(scoreDocs))
        query = QueryParser('contents', analyzer).parse(command)

        titlst = []
        urlst = []
        timlst = []
        contentlist = []
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
            title = doc.get('title')
            url = doc.get('url')
            tt = doc.get('date')
            contents = urllib.request.urlopen(url)
            soup =  BeautifulSoup(contents,features="html.parser")
            contents = ''.join(soup.findAll(text=True))
            contents = ' '.join(jieba.cut(contents))
            titlst.append(title)
            urlst.append(url)
            timlst.append(tt)
            contentlist.append(contents)

        if mode == "time":
            for i in range(len(urlst)):
                for j in range(len(urlst)-1-i):
                    if timeCompare(timlst[j], timlst[j+1]) == 0:
                        titlst[j], titlst[j+1] = titlst[j+1], titlst[j]
                        timlst[j], timlst[j+1] = timlst[j+1], timlst[j]
                        urlst[j], urlst[j+1] = urlst[j+1], urlst[j]
                        contentlist[j], contentlist[j+1] = contentlist[j+1], contentlist[j]


        # for scoreDoc in scoreDocs:
        for i in range(len(urlst)):
            title = titlst[i]
            url = urlst[i]
            tt = timlst[i]
            contents = contentlist[i]
 

            formatter = SimpleHTMLFormatter('"','"')           #           1
            highlighter =  Highlighter(formatter,QueryScorer(query))   
            highlighter.setTextFragmenter(SimpleFragmenter(25))
            tmp = analyzer.tokenStream("contents",contents)                #           1
            substring = highlighter.getBestFragment(tmp,contents)

            if substring !=None:
                con.append(substring)   
            else:
                continue
            tll.append(title)
            uu.append(url)
            time.append(tt)            
        break

app = Flask(__name__)
@app.route('/', methods=['POST', 'GET'])
def bio_data_form():
    if request.method == "POST":
        keyword = request.form['keyword']
        mode = request.form['mode']
        return redirect(url_for('result', keyword=keyword))
    return render_template("bio_form.html")


@app.route('/result', methods=['GET'])
def result():
    
    global tll,uu,con,time, last_search
    STORE_DIR = "163_index"

    vm.attachCurrentThread()   #一旦线程被附加到JVM上，这个函数会返回一个属于当前线程的JNIEnv指针

    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    # analyzer = StandardAnalyzer()
    analyzer = SimpleAnalyzer()

    keyword = request.args.get('keyword')
    if keyword == '':
        keyword = last_search
    elif keyword != '':
        last_search = keyword
    keyword = ' '.join(jieba.cut(keyword))

    mode = request.args.get('mode')

    runs(searcher, analyzer,keyword, mode)
    length = min(len(tll),len(uu))
    length = min(length,len(con))
    length = min(length,len(time))
    del searcher
    return render_template("result.html",keyword=keyword,length = length,uu=uu,tll=tll,con=con,time = time)





if __name__ == '__main__':
    last_search = ''

    vm = lucene.initVM()

    app.run(debug=True,port = 8081)
    
    