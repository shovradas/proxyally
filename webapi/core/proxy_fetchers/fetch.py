from scrapy.crawler import CrawlerProcess
import sys
from importlib import import_module

class ItemCollectorPipeline():
    items = []

    def process_item(self, item, spider):
        ItemCollectorPipeline.items.append(item)

    def close_spider(self, spider):
        print(ItemCollectorPipeline.items)


if __name__ == '__main__':
    spider_name = sys.argv[1]
    mdl = import_module('.'.join(spider_name.split('.')[:-1])) # modulen name example: core.proxy_fetchers.proxydashlistdownload
    spider = getattr(mdl, spider_name.split('.')[-1]) # class name

    process = CrawlerProcess({
        'USER_AGENT': 'scrapy',
        'LOG_LEVEL': 'WARNING',
        'ITEM_PIPELINES': { '.'.join([__name__, ItemCollectorPipeline.__name__]): 100 } 
    })
    process.crawl(spider)
    process.start()