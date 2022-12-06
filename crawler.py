# SJTU EE208

from logging import exception
import ssl
import os
import re
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
import queue
import threading
from bs4 import BeautifulSoup
def find_date(page): #从网址字符串中找到日期（仅在新浪体育的搜索中匹配）
    for i in range(len(page)-5):
        if page[i]=='-':
            if page[i+3]=='-':
                try:
                    a,b,c = int(page[i-4:i]),int(page[i+1:i+3]),int(page[i+4:i+6])
                    return page[i-4:i+6]
                except BaseException:
                    return ''
                

def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars) + '.txt'
    return s

def get_page(page):
    try:
        header = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"}
        request = urllib.request.Request(page, headers=header)
        content = urllib.request.urlopen(request).read()
    except TimeoutError:
        return 0
    except BaseException:
        return 0
    return content


def get_all_links(content, page):
    soup = BeautifulSoup(content,features='html.parser')
    outlinks = []
    for link in soup.find_all('a'):
        link = link.get('href')
        if not link:
            continue
        elif link[0]=='/' and link != '/':
            link = urllib.parse.urljoin(page, link)
            if 'sports.163.com' in link or 'www.163.com/sports' in link:
                #sports.sina.com.cn  腾讯体育
                #sports.163.com or www.163.com/sports 网易体育
                outlinks.append(link)
        elif link != 'javascript:;':
            if 'sports.163.com' in link or 'www.163.com/sports' in link:
                outlinks.append(link)
    return outlinks


def add_page_to_folder(page, content):  # 将网页存到文件夹里，将网址和对应的文件名写入index.txt中
    if 'article' not in page:
        return True
    index_filename = '163_index.txt' # index.txt中每行是'网址 对应的文件名' 图片index与此相同
    folder = '163_html'  # 存放网页的文件夹
    graphfolder = '163_graph_html' #存放图片的文件夹
    filename = valid_filename(page) # 将网址变成合法的文件名
    soup = BeautifulSoup(content,features='html.parser')
    title = soup.find('title') #新闻标题
    if title:
        title = title.text
    t = ''
    for i in soup.findAll('meta'):
        if i.get('property','') =='article:published_time':
            t = i.get('content','')[0:10] #新闻时间
            break
    else:
        t = find_date(page)
    if title and t: #两者都存在，才写入文件
        index = open(index_filename, 'a')
        index.write(str(page.encode('ascii', 'ignore')) + '\t' + filename + '\n')
        index.close()
        if not os.path.exists(folder):  # 如果文件夹不存在则新建
            os.mkdir(folder)
        if not os.path.exists(graphfolder):  # 如果文件夹不存在则新建
            os.mkdir(graphfolder)
        try:
            f = open(os.path.join(folder, filename), 'w')
            g = open(os.path.join(graphfolder,filename), 'w')
        except BaseException:
            return False
        f.write(page+'\n') #写入当前网页
        g.write(page+'\n')
        f.write(title+'\n') #写入网页标题
        g.write(title+'\n')
        f.write(t+'\n') #写入文章时间
        g.write(t+'\n')
        texts = soup.findAll(text=True)
        text = []
        for t in texts:
            y = t.parent.name
            if y in ['p','h1','strong']:
                text.append(t)
        t = ''.join(text)
        t = t.replace('\r','').replace('\n','').replace('\t','')
        f.write(t)  # 将网页内容存入文件
        for i in soup.findAll('img'):
            img = i.get('src', '')
            text = i.get('alt', '')
            """         
            if not text:
                i = i.parent
                while not i.text:
                    i = i.parent
                text = i.text   #查找外圈文本
            if not text:
                text = title #实在查找不到时，用标题作为文本
            """ #仅在新浪网时用到
            text = text.replace('\r','').replace('\n','').replace('\t','') #消除不必要的字符
            g.write(img+'\t')
            g.write(text+'\n')
        f.close()
        g.close()
    elif not t:
        print("no time value!")
    else:
        print("no title!")
    return True

def crawl():
    global crawled
    while True:
        page = q.get()
        if page not in crawled:
            crawled.append(page)
            l=len(crawled)
            print(l,page)
            content = get_page(page)
            if content != 0:
                if add_page_to_folder(page, content):
                    outlinks = get_all_links(content, page)
                    for link in outlinks:
                        q.put(link)
                    if len(crawled) >= max_page:
                        return
            q.task_done()

varLock = threading.Lock()
max_page = 150000
count = 0
NUM = 100
crawled = []
q = queue.Queue()
q.put('https://sports.163.com')
#https://sports.sina.com.cn/           新浪体育
#https://sports.163.com                网易体育
for i in range(NUM):
    t = threading.Thread(target=crawl)
    t.setDaemon(True)
    t.start()
for i in range(NUM):
    t.join()
#https://news.cctv.com

