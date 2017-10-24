# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from contextlib import contextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler

import scrapy
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from sqlalchemy.orm import sessionmaker

from tutorial.models import db_connect, create_news_table, ACComment

formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
handler = RotatingFileHandler("Pipeline.log", maxBytes=3 * 1024 * 1024)
handler.setFormatter(formatter)
pipelineLogging = logging.getLogger("Pipeline")
pipelineLogging.addHandler(handler)
# LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

class CachePipeline(object):
    # def __init__(self):
    # print("CachePipeline init")
    def open_spider(self, spider):
        self._lru = spider._cache
        print("CachePipeline opend")

    # def close_spider(self, spider):
    #     print("CachePipeline closed")

    # def process_item(self, item, spider):
    #     cid = item['cid']
    #     self._lru[cid]=item
    #     lruItem = self._lru.get(cid, None)
    #     pipelineLogging.info("=========== CachePipeline Find deleted item= " + str(lruItem))
    #     del self._lru[cid]
    #     pipelineLogging.info("Delete item %s in LRU, \n Now size is %s" % (str(lruItem), len(self._lru)))
    #     return lruItem

    def process_item(self, item, spider):
        cid = item['cid']
        # print("CachePipeline Processing..id= " + str(cid))
        isDelete = item['isDelete'] or item['isUpDelete'] or item['userID'] == -1
        lruItem = self._lru.get(cid, None)
        if(isDelete and lruItem):
            pipelineLogging.info("=========== CachePipeline Find deleted item= " + str(lruItem))
            lruItem['isDelete'] = item['isDelete']
            lruItem['isUpDelete'] = item['isUpDelete']
            del self._lru[cid]
            pipelineLogging.info("Delete item %s in LRU, \n Now size is %s" % (str(lruItem), len(self._lru)))
            return lruItem
        else:
            if(not isDelete):
                self._lru[cid]=item
                if(not lruItem):
                    pipelineLogging.info("Add item to LRU, now size is %s" % len(self._lru))
            raise DropItem("Duplicate item found: cid = %s" % cid)


@contextmanager
def session_scope(Session):
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class DBPipeline(object):

    def __init__(self):
        # engine = create_engine('mysql+mysqldb://root:ali88@localhost/actest', echo=True)
        engine = db_connect()
        create_news_table(engine)
        self.Session = sessionmaker(bind=engine)
        # print("DBPipeline init")

    # def open_spider(self, spider):
    #     pipelineLogging.info("DBPipeline opend")
    #
    # def close_spider(self, spider):
    #     pipelineLogging.info("DBPipeline closed")

    def process_item(self, item, spider):

        item['updateDate'] = datetime.now()
        accmt = ACComment(**item)
        with session_scope(self.Session) as session:
            session.add(accmt)
        pipelineLogging.info("Item saved: %s" % str(item))
        return item


class MyImagesPipeline(ImagesPipeline):
    """先安装：pip install Pillow"""

    def get_media_requests(self, item, info):
        image_url = item['userImg']
        return [scrapy.Request(image_url)]

    def item_completed(self, results, item, info):
        if(results[0][0]):
            item['localImgPath'] = results[0][1]['path']

        pipelineLogging.info("MyImagesPipeline item_completed item %s " % str(item['cid']))
        return item
