#!/usr/bin/env python
# _*_ coding:UTF-8

'''
Created on 2013-8-10

@author: osdba
@modify: osdba
'''

import threading
import urllib2
import BeautifulSoup
import Queue
import signal
import os
import time
import traceback

class MemKV():
    '''支持多线程并发访问的字典
    '''
    
    def __init__(self):
        '''初使用化函数
        '''
        
        self.lock = threading.Lock()
        self.db =  {}
    
    def get(self, key, default=None):
        '''KV中的get函数
        
        @param key KV存取中的key
        @param default 当key不存在时，返回此值
        @return 如果key不存在，则返回default
        '''
        
        self.lock.acquire()
        try:
            value = self.db.get(key, default)
        finally:
            self.lock.release()
        return value

    def set(self, key, value):
        '''KV操作中的set函数
        
        @param key KV存取中的key
        @param value KV存取中的value，如果value为None，则会删除此key
        '''
        self.lock.acquire()
        try:
            if value is None:
                if self.db.has_key(key):
                    del self.db[key]
            else:
                self.db[key] = value
        finally:
            self.lock.release()

    def hasKey(self, key):
        '''KV操作中的set函数
        
        @param key KV存取中的key
        @param value KV存取中的value，如果value为None，则会删除此key
        '''
        self.lock.acquire()
        try:
            if self.db.has_key(key):
                return True
            else:
                return False
        finally:
            self.lock.release()
            
            
    def notInAndSet(self, key, value):
        '''当key存在，则返回，不存在则插入
        
        @param key KV存取中的key
        @param value KV存取中的value，如果value为None，则会删除此key
        '''
        if value is None:
            return

        self.lock.acquire()
        try:
            if self.db.has_key(key):
                return False
            else:
                self.db[key] = value
                return True
        finally:
            self.lock.release()


class MyThreadPool():
    '''一个简单的线程池的类'''
    
    def __init__(self, *args, **kwargs):
        self.clients = Queue.Queue()
        self.threads = 50
        self.daemon = kwargs.get("daemon", False)
    
    def setNumThreads(self, num):
        '''Set the number of worker threads that should be created'''
        self.threads = num
    
    def serveThread(self):
        '''Loop around getting clients from the shared queue and process them.'''
        while True:
            try:
                client = self.clients.get()
                #logger.debug("serveThread,the function:%s,the args:%s" % (str(client[0]), str(client[1])))
                client[0](client[1]) 
            except Exception:
                print traceback.format_exc()
                #logger.exception(x)
        
    def startPool(self):
        '''Start a fixed number of worker threads and put client into a queue'''
        
        for i in range(self.threads):
            try:
                t = threading.Thread(target = self.serveThread)
                t.setDaemon(self.daemon)
                t.start()
            except Exception, x:
                print x
    
    def addJob(self, jobFunc, jobArgs):
        client=[]
        client.append(jobFunc)
        client.append(jobArgs)
        self.clients.put(client)


def downloadWebAndChild(args):
    '''下载一个网页和它网页中的链接指向的子网页（子网页要求是本网站的，不是本网站的不会下载），会递归
    '''

    db, threadPool, baseUrl, fileName, downloadPath = args
    url = "%s%s" % (baseUrl, fileName)
    #print "download: %s" % fileName
    i = 0
    cnt = 3
    while i < cnt:
        try:
            req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
            webPage= urllib2.urlopen(req)
            webData = webPage.read()
            dirPath = os.path.dirname(fileName)
            if len(dirPath) > 0 and not os.path.exists(dirPath):
                os.makedirs(dirPath)
            break
        except HTTPError, e:
            print repr(e)
            i = i + 1
        except Exception, e:
            print repr(e)
            i = i + 1
        time.sleep(1)
    
    f = open("%s/%s" % (downloadPath, fileName), "w")
    f.write(webData)
    f.close()
    
    soup = BeautifulSoup.BeautifulSoup(webData)
    #print "find url in %s: " % fileName    
    aList =  soup.findAll('a')
    for link in aList:
        href = link.get('href')
        print "    href=%s" % href
        if href is None:
            continue
        if href[:7] == 'mailto:':
            continue
        if '://' in href:
            continue
        baseName = os.path.basename(href)
        if '#' in href:
            childFileName = href[:href.index('#')]
        else:
            childFileName = href

        if len(childFileName)<=0:
            print "href=%s, childFileName=%s" % (href, childFileName)
            continue

        if not db.notInAndSet(childFileName,'u'):
            continue

        #print "add job(%s)" % childFileName
        threadPool.addJob(downloadWebAndChild, [db, threadPool, baseUrl, childFileName, downloadPath])
        #print "process url %s finished." % fileName

def sigHandle(signum=0, e=0):
    '''signal handle'''

    print "========== Recv signal %d, program is stop. ==========" % signum
    os._exit(0)

        
def main():

    signal.signal(signal.SIGINT, sigHandle)
    signal.signal(signal.SIGTERM, sigHandle)
    
    threadPool = MyThreadPool()
    threadPool.startPool()
    #从瀚高下载PostgreSQL9.0中文帮助
    baseUrl = "http://www.highgo.com.cn/docs/docs90cn/"
    fileName = "index.html"
    #下载下来的文件放在当前目录下的子目录htmlorigin
    downloadPath = "htmlorigin"
    
    db = MemKV()
    db.notInAndSet(fileName,'u')
    threadPool.addJob(downloadWebAndChild, [db, threadPool, baseUrl, fileName, downloadPath])
    
    while True:
        qsize = threadPool.clients.qsize()
        print "%d task in queue wait for download..." % qsize
        time.sleep(2)

if __name__ == "__main__":
    main()

