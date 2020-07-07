import scrapy, os, json
from urllib.parse import urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyRssSpider(scrapy.spiders.feed.XMLFeedSpider):
    name = 'xroxycom'

    itertag = 'prx:proxy'
    iterator = 'xml'
    namespaces = [
        ('content', 'http://purl.org/rss/1.0/modules/content/'),
        ('prx', 'http://www.proxyrss.com/content')
    ]

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/xroxycom.xml'))
            yield scrapy.Request(url)
        else:
            yield scrapy.Request('https://www.xroxy.com/proxyrss.xml')

    def parse_node(self, response, node):
        yield {
                'ip': node.xpath('prx:ip/text()').get(),
                'port': int(node.xpath('prx:port/text()').get())
            }


def fetch(config):
    ProxyRssSpider.custom_settings = {
        'DOWNLOAD_DELAY': config['downloadDelay']
    }
    # core.proxy_fetchers.proxydashlistdownload.ProxyApiSpider
    spider = '.'.join([__name__, ProxyRssSpider.__name__])
    data = os.popen(f'python {os.getcwd()}/core/proxy_fetchers/fetch.py {spider}').read()
    return  ast.literal_eval(data)


if __name__ == '__main__':
    data = fetch()
    print(json.dumps(data, indent=4), f'count: {len(data)}')