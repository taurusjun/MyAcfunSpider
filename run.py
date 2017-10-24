#!/usr/bin/python
#coding=utf8

import shlex, subprocess
from lru import LRU

import schedule as schedule
import time
import logging
from logging.handlers import RotatingFileHandler

from scrapy import cmdline, signals
from scrapy.crawler import Crawler, CrawlerRunner,CrawlerProcess
from sqlalchemy.orm import sessionmaker
from twisted.internet import reactor, task
from scrapy.utils.project import get_project_settings

from tutorial.models import db_connect, ACComment, ACCommentCache, create_news_table
from tutorial.spiders.acfun_spider import AcfunSpider, AcfunItem, AcfunCommentItem
from datetime import timedelta, datetime

mLRU = LRU(102400)
CONTROL='control'

formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
handler = RotatingFileHandler("Run.log", maxBytes=3 * 1024 * 1024)
handler.setFormatter(formatter)
runLogging = logging.getLogger("Run")
runLogging.addHandler(handler)


def checkIfToStopRun():
    f = open(CONTROL, 'r+')
    c = f.readline()
    if c!='' and str(c)=='-1':
        onShutDown()
        reactor.stop()
        print ("Stop reactor!")


def saveLRUItems():
    engine = db_connect()
    create_news_table(engine)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    itemCount = len(mLRU)
    for itm in mLRU.values():
        accmt = ACCommentCache(**itm)
        session.merge(accmt)
    session.commit()
    session.close()
    runLogging.info("%s items saved, before stop the reactor!" % itemCount)


def loadLRUItems():
    engine = db_connect()
    create_news_table(engine)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # query = session.query(ACComment).filter(ACComment.postDate+timedelta(hours=1) > datetime.now())
    # items = query.all()
    mysqlClause = "SELECT * FROM actest2.accommentcache where postDate > DATE_SUB(NOW(), INTERVAL 1 day)  order by postDate asc"
    accItems = session.execute(mysqlClause).fetchall()
    for accItm in accItems:
        itm = AcfunCommentItem()
        itm['cid']=accItm[0]
        itm['acid'] = accItm[1]
        itm['quoteId'] = accItm[2]
        itm['content'] = accItm[3]
        itm['postDate'] = accItm[4]
        itm['userID'] = accItm[5]
        itm['userName'] = accItm[6]
        itm['userImg'] = accItm[7]
        itm['localImgPath'] = accItm[8]
        itm['count'] = accItm[9]
        itm['deep'] = accItm[10]
        itm['refCount'] = accItm[11]
        itm['ups'] = accItm[12]
        itm['downs'] = accItm[13]
        itm['nameRed'] = accItm[14]
        itm['avatarFrame'] = accItm[15]
        itm['isDelete'] = accItm[16]
        itm['isUpDelete'] = accItm[17]
        itm['nameType'] = accItm[18]
        itm['verified'] = accItm[19]
        cid = itm['cid']
        mLRU[cid] = itm
    itemCount = len(accItems)
    print ("%s items loaded, before start the reactor!" % itemCount)
    runLogging.info("%s items loaded, before start the reactor!" % itemCount)
    session.close()

def onShutDown():
    saveLRUItems()
    mLRU.clear()

def crawl_work():
    # cmdline.execute('scrapy crawl acfun'.split())
    # command_line = "scrapy crawl acfun"
    # args = shlex.split(command_line)
    # p = subprocess.Popen(args) # Execute a child program in a new process.
    settings = get_project_settings()
    crawler = CrawlerProcess(settings)
    # crawler = CrawlerRunner(settings)
    crawler.crawl(AcfunSpider, cache=mLRU)
    # crawler.start()
    checkIfToStopRun()

def crawl_work_singleRun():
    settings = get_project_settings()
    crawler = CrawlerProcess(settings)
    # crawler = CrawlerRunner(settings)
    crawler.crawl(AcfunSpider, cache=mLRU)
    crawler.start()
    saveLRUItems()
    mLRU.clear()


if __name__=='__main__':
    loadLRUItems()
    # 定时跑
    lc = task.LoopingCall(crawl_work)
    lc.start(5)
    print ("Start reactor!")
    reactor.addSystemEventTrigger('before', 'shutdown', onShutDown)
    reactor.run()

    #单跑
    # crawl_work_singleRun()

    print ("all finished!")
