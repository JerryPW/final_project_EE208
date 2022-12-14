# SJTU EE208
INDEX_DIR = "IndexFiles.index"

import re

# for paragraph searching
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

# for picture searching
import time
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
from torchvision.datasets.folder import default_loader
import PIL
import os
import numpy as np
import cv2

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

def urlToarray(url):
    cap = cv2.VideoCapture(url)
    if( cap.isOpened() ) :
        ret,img = cap.read()
        cv2.waitKey()
        return img

def queryPicture(picture, model, trans):
    def extract(img):
        print('Prepare image data!')
        cap = cv2.VideoCapture(img)
        img1 = None
        if( cap.isOpened() ) :
            ret,img1 = cap.read()
            cv2.waitKey()
        cv2.imwrite("temp.png", img1)
        test_image = default_loader("temp.png")
        input_image = trans(test_image)
        input_image = torch.unsqueeze(input_image, 0)


        def features(x):
            x = model.conv1(x)
            x = model.bn1(x)
            x = model.relu(x)
            x = model.maxpool(x)
            x = model.layer1(x)
            x = model.layer2(x)
            x = model.layer3(x)
            x = model.layer4(x)
            x = model.avgpool(x)

            return x


        print('Extract features!')
        start = time.time()
        image_feature = features(input_image)
        image_feature = image_feature.detach()
        image_feature = torch.reshape(image_feature, ((2048, )))

        print('Time for extracting features: {:.2f}'.format(time.time() - start))
        return np.array(image_feature)
    
    def similarity(feature1, feature2):
        feature1 = np.array(feature1)
        feature2 = np.array(feature2)
        result = (feature1 - feature2)**2
        result = np.sum(result, axis=1)
        result = np.sqrt(result)
        return result
    
    pic_feature = extract(picture)
    matched_url = []
    
    # 匹配10张
    times = 0
    for root, dirs, files in os.walk("163_graph_html", topdown=False):
        for name in files:
            f = open(os.path.join(root, name),'r')
            contents = f.readlines()
            for i in range(5, len(contents)):
                pos = contents[i].find('\t')
                url = contents[i][0:pos]
                img_feature = extract(url)
                
                if(similarity(img_feature, pic_feature) < 4):
                    matched_url.append(str(url))
                    times += 1
                if times == 10:
                    break
            if times == 10:
                break    
    matched_url = np.array(matched_url)
    return matched_url

app = Flask(__name__)
@app.route('/', methods=['POST', 'GET'])
def bio_data_form():
    if request.method == "POST" and request.form['keyword'] != '':
        print("#######################################################")
        keyword = request.form['keyword']
        mode1 = request.form['mode1']
        mode2 = request.form['mode2']
        return redirect(url_for('result', keyword=keyword, mode1=mode1, mode2=mode2))
    elif request.method == "POST" and request.form['keyword'] == '':
        pic = request.form['file']
        return redirect(url_for('picture', pic=pic))
    return render_template("bio_form.html")

@app.route('/picture', methods=['GET'])
def picture():
   pic = request.args.get('picture') # 得到照片的url
   #pic = urlToarray(pic) # get the array
   model = torch.hub.load('pytorch/vision', 'resnet50', pretrained=True)
   
   vm.attachCurrentThread()

   normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])
   trans = transforms.Compose([
   transforms.Resize(256),
   transforms.CenterCrop(224),
   transforms.ToTensor(),normalize,])
   
   print(pic)
   return
   
   searchResult = queryPicture(pic, model, trans)  # 返回url链接的列表
   length = len(searchResult)
   return render_template('picture.html', searchResult=searchResult, length=length)
    
    
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

    mode1 = request.args.get('mode1')
    mode2 = request.args.get('mode2')
    mode = None
    if mode2 == 'time':
        mode = mode2
    else:
        mode = mode1

    runs(searcher, analyzer,keyword, mode)
    length = min(len(tll),len(uu))
    length = min(length,len(con))
    length = min(length,len(time))
    del searcher
    return render_template("result.html",keyword=keyword,length = length,uu=uu,tll=tll,con=con,time = time)





if __name__ == '__main__':
    last_search = ''

    vm = lucene.initVM()

    app.run(debug=True,port = 8083)
    
    