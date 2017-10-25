#!/usr/bin/python
#coding=utf8

import scrapy
import re
import json

from scrapy.spiders import CrawlSpider

from tutorial.items import *


class AcfunSpider(CrawlSpider):
    name = "acfun"
    # allowed_domains = ["dmoz.org"]
    start_urls = [
        # "http://www.dmoz.org/Computers/Programming/Languages/Python/Books/",
        # "http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/"
        "http://www.acfun.cn/v/list110/index.htm"
        # "http://www.acfun.cn/a/ac3998668"
    ]

    def __init__(self, *args, **kwargs):
        super(AcfunSpider, self).__init__(*args, **kwargs)
        self._cache = kwargs.get('cache')
        # self.log('Hi, we get acfun spider!')

    def parse(self, response):
        # body_data = response.body;
        # parse_data = self.get_parse_data(body_data);
        # self.log('Hi, we get response!')
        replyListItems = self.parse_reply_list(response)
        for itm in replyListItems:
            acid = itm['link'][0][5:]
            url = "http://www.acfun.cn/comment_list_json.aspx?contentId=" + str(acid) + "&currentPage=1"
            yield scrapy.Request(url, meta={'acid':str(acid)}, callback=self.parse_comment_contents)

        # print 1
        # filename = response.url.split("/")[-2]
        # with open(filename, 'wb') as f:
        #     f.write(response.body)

    # 主内容区：xpath: '//div[@id="mainer"]//div[@id="block-content-article"]//div[@class="mainer"]/div[@class="item"]/a/@href'
    # 最新回复区：xpath: //div[@id="mainer"]//div[@id="block-reply-article"]//div[@class="mainer"]//a/@href'
    def parse_reply_list(self, response):
        for sel in response.xpath('//div[@id="mainer"]//div[@id="block-reply-article"]//div[@class="mainer"]//a'):
            item = AcfunItem()
            item['title'] = sel.xpath('@title').extract()
            item['link'] = sel.xpath('@href').extract()
            yield item

    # 解析评论
    def parse_comment_contents(self,response):
        acid = response.meta['acid']
        jsonresponse = json.loads(response.body_as_unicode())
        responseStatus = jsonresponse[u'status']
        responseSuccess = jsonresponse[u'success']
        if responseStatus == 200 and responseSuccess == True:
            commentsList = jsonresponse[u'data'][u'commentContentArr']
            # 开始解析json评论
            for m, n in enumerate(commentsList):
                commentJson = commentsList[n]
                commentItem = AcfunCommentItem(commentJson)
                # 设定acid
                commentItem['acid'] = acid
                # 默认是float，转成long
                commentItem['cid'] = long(commentItem['cid'])
                commentItem['quoteId'] = long(commentItem['quoteId'])
                commentItem['userID'] = long(commentItem['userID'])
                yield commentItem
