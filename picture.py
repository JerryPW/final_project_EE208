import os
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import requests
import cv2


times = 1
for root, dirs, files in os.walk("163_graph_html", topdown=False):
    for name in files:
        f = open(os.path.join(root, name),'r')
        contents = f.readlines()
        for i in range(5, len(contents)):
            pos = contents[i].find('\t')
            url = contents[i][0:pos]
            cap = cv2.VideoCapture(url)
            if( cap.isOpened() ) :
                ret,img = cap.read()
                cv2.waitKey()
            