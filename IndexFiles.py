# SJTU EE208

INDEX_DIR = "IndexFiles.index"

import sys, os, lucene, threading, time
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.error
import urllib.parse
import urllib.request
import jieba
from urllib.parse import urlparse

# from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import WhitespaceAnalyzer, SimpleAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, StringField, TextField
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.analysis.core import SimpleAnalyzer

"""
This class is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.IndexFiles.  It will take a directory as an argument
and will index all of the files in that directory and downward recursively.
It will index on the file path, the file name and the file contents.  The
resulting Lucene index will be placed in the current directory and called
'index'.
"""

class Ticker(object):

    def __init__(self):
        self.tick = True

    def run(self):
        while self.tick:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.0)

class IndexFiles(object):
    """Usage: python IndexFiles <doc_directory>"""

    def __init__(self, root, storeDir):

        if not os.path.exists(storeDir):
            os.mkdir(storeDir)

        # store = SimpleFSDirectory(File(storeDir).toPath())
        store = SimpleFSDirectory(Paths.get(storeDir)) #索引文件存放的位置
        analyzer = WhitespaceAnalyzer()
        analyzer = LimitTokenCountAnalyzer(analyzer, 1048576)
        #analyzer是用来对文档进行词法分析和语言处理的
        config = IndexWriterConfig(analyzer)
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
        writer = IndexWriter(store, config)
        #创建一个IndexWriter用来写索引文件
        self.indexDocs(root, writer)
        ticker = Ticker()
        print('commit index')
        threading.Thread(target=ticker.run).start()
        writer.commit()
        writer.close()
        ticker.tick = False
        print('done')

    def indexDocs(self, root, writer):
        t1 = FieldType()
        t1.setStored(True)
        t1.setTokenized(False)
        t1.setIndexOptions(IndexOptions.NONE)  # Not Indexed
        
        t2 = FieldType()
        t2.setStored(False)
        t2.setTokenized(True)
        t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)  # Indexes documents, frequencies and positions.
        print("here1")
        print(os.walk(root))
        for root, dirnames, filenames in os.walk(root):
            print("here2")
            for filename in filenames:
                # if not filename.endswith('.txt'):
                #     continue
                print("adding", filename)
                try:
                    path = os.path.join(root, filename)
                    file = open(path, encoding='utf8')
                    contents = file.read()
                    contents = ' '.join(jieba.cut(contents))
                    file.close()
                    doc = Document()
                    doc.add(Field("name", filename, t1))
                    doc.add(Field("path", path, t1))
                    f = open("index.txt", 'r')
                    for i in f.readlines():
                        lst = i.split('\t')
                        if (lst[1][:-1] == filename):
                            doc.add(Field("url", lst[0], t1))
                            site = urlparse(lst[0]).netloc
                            site = ' '.join(site.split('.'))
                            doc.add(Field("site", site, t2))
                            #doc.add(TextField('url', lst[0], Field.Store.YES))
                            soup = BeautifulSoup(urllib.request.urlopen(lst[0]).read(),features="html.parser")
                            tit = soup.head.title.string
                            doc.add(Field("title", tit, t1))
                            break
                    f.close()
                    if len(contents) > 0:
                        #doc.add(TextField('contents', contents, Field.Store.YES))
                        doc.add(Field("contents", contents, t2))
                    else:
                        print("warning: no content in %s" % filename)
                    writer.addDocument(doc)
                except Exception as e:
                    print("Failed in indexDocs:", e)

if __name__ == '__main__':
    lucene.initVM()#vmargs=['-Djava.awt.headless=true'])
    print('lucene', lucene.VERSION)
    # import ipdb; ipdb.set_trace()
    start = datetime.now()
    try:
        IndexFiles('html', "index")
        end = datetime.now()
        print(end - start)
    except Exception as e:
        print("Failed: ", e)
        raise e

