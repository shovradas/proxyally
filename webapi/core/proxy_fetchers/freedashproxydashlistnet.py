import scrapy, os, json
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyScrapSpider(scrapy.Spider):
    name = 'freedashproxydashlistnet'

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/freedashproxydashlistnet.html'))
            yield scrapy.Request(url, self.parse)
        else:
            yield scrapy.Request('https://free-proxy-list.net/', self.parse)

    def parse(self, response):
        table = response.xpath('//table[@id="proxylisttable"]')
        trs = table.xpath('tbody/tr')
        for tr in trs:
            tds = tr.xpath('td')
            yield {
                'ip': tds[0].xpath('text()').extract_first(),
                'port': int(tds[1].xpath('text()').extract_first()),
                'code': tds[2].xpath('text()').extract_first(),
                'country': tds[3].xpath('text()').extract_first(),
                'anonymity': tds[4].xpath('text()').extract_first().strip(' proxy'),
                'https': tds[6].xpath('text()').extract_first()
            }


def fetch(config):
    ProxyScrapSpider.custom_settings = {
        'DOWNLOAD_DELAY': config['downloadDelay']
    }
    # core.proxy_fetchers.proxydashlistdownload.ProxyApiSpider
    spider = '.'.join([__name__, ProxyScrapSpider.__name__])
    data = os.popen(f'python {os.getcwd()}/core/proxy_fetchers/fetch.py {spider}').read()
    return  ast.literal_eval(data)


if __name__ == '__main__':
    data = fetch()
    print(json.dumps(data, indent=4), f'count: {len(data)}')