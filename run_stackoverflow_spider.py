from scrapy import cmdline

cmdline.execute("scrapy crawl stackoverflow -o top-stackoverflow-questions.json".split())
