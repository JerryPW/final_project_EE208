# SJTU EE208
INDEX_DIR = "IndexFiles.index"

import sys, os, lucene,jieba
from org.apache.lucene.search.highlight import Highlighter
from java.io import File
from java.nio.file import Path
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import SimpleAnalyzer, WhitespaceAnalyzer
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
titlst = []
urlst = []
commandlst = []

#搜索部分
def parseCommand(command):
    allowed_opt = ['site']
    opt = 'contents'
    command_dict = {opt: ''}
    for i in command.split(' '):
        if ':' in i:
            opt, value = i.split(':')[:2]
            opt = opt.lower()
            if opt == 'site':
                value = ' '.join(value.split('.'))
            if opt in allowed_opt and value != '':
                command_dict[opt] = value
        else:
            command_dict[opt] = command_dict.get(opt, '') + ' ' + i
    command_dict['contents'] = ' '.join(jieba.cut(command_dict['contents']))
    return command_dict

def runs(searcher, analyzer, command):
    global title,url
    global titlst,urlst,commandlst
    titlst = []
    urlst = []
    commandlst = []
    while True:
        print()
        print ("Hit enter with no input to quit.")
        # command = unicode(command, 'GBK')
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
        formatter = SimpleHTMLFormatter("“","“")   # 如何高亮匹配的关键字
        highlighter =  Highlighter(formatter,QueryScorer(query))
        highlighter.setTextFragmenter(SimpleFragmenter(30))
        
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
            title = doc.get('title')
            url = doc.get('url')
            contents = urllib.request.urlopen(url)
            soup =  BeautifulSoup(contents,features="html.parser")
            contents = ''.join(soup.findAll(text=True))
            contents = ' '.join(jieba.cut(contents))
            
            string = analyzer.tokenStream("contents",contents)
            substring = highlighter.getBestFragment(string,contents)
            if substring==None:
                continue
            else:
                commandlst.append(substring)
            titlst.append(title)
            urlst.append(url)
                    
        break


# 渲染部分 + 提交部分
app = Flask(__name__)
@app.route('/', methods=['POST', 'GET'])
def bio_data_form():
    if request.method == "POST":
        keyword = request.form['keyword']
        return redirect(url_for('result', keyword=keyword))
    return render_template("bio_form.html")

@app.route('/result', methods=['GET'])
def result():
    global titlst,urlst,commandlst
    STORE_DIR = "index"

    initial_vm.attachCurrentThread()
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()
    keyword = request.args.get('keyword')
    keyword = ' '.join(jieba.cut(keyword))

    
    runs(searcher, analyzer,keyword)
    # length = min(len(titlst),len(urlst))
    # length = min(length,len(commandlst))
    length = min(min(len(titlst), len(urlst)), len(commandlst))
    del searcher
    return render_template("result.html",keyword=keyword,length = length,u=urlst,t=titlst,c=commandlst)


if __name__ == '__main__':
    initial_vm = lucene.initVM()
    app.run(debug=True,port = 8088)
    
    
    