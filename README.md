# final_project_EE208
This is the final project for class EE208 in SJTU.

We will build a website for searching latest sport news, and this project has been just started.

Hope for more progress!

---
项目描述
在本次项目中，我们先利用并行式爬虫爬取1w余体育网页和网页中对应的大量图像。然后对这些新闻 数据进行解析，并建立索引。在搜索引擎的创立过程中，我们利用lucene进行关键词查询，利用通过 ResNet50模型提取图像特征信息，并基于LSH算法进行图片搜索。整个网页采用Flask库进行搭建，并 借助bootstrap框架优化页面设计。

---
本次大作业完成的功能：
1. 新闻索引的创建及基于关键词搜索
    > 搜索引擎
    > 按时间，相关度的排序
2. 利用LSH的以图搜图
3. 相似新闻的自动聚类

---
大作业运行环境：
1. openCV，NumPy，Matplotlib，jieba，Flask，Levenshtein
2. Docker配置的sjtucmic/ee208镜像环境 ps:Levenshtein库需要下载，在docker中并无

---
如何运行：
1. 下载好所有文件，并放置进一个文件夹中。
2. 利用vscode打开该文件夹，并打开docker，令其open in container
3. 运行app.py，在右下角弹出提示框中选择在浏览器中运行即可

