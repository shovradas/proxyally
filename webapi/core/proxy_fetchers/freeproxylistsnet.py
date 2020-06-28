import scrapy, os, json
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyScrapSpider(scrapy.Spider):
    name = 'freeproxylistsnet'
    page_number=2
    max_page=3

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/freeproxylistsnet.html'))
            yield scrapy.Request(url, self.parse)
        else:
            yield scrapy.Request('http://www.freeproxylists.net/', self.parse)


    def parse(self, response):
        table = response.xpath('//table[@class="DataGrid"]')[0]   
        trs = table.xpath('tr')
        for tr in trs:
            tds = tr.xpath('td')
            if len(tds)>1:
                ip_text = tds[0].xpath('script/text()').extract_first()
                if ip_text:                    
                    ip_text = unquote(ip_text.split('"')[1])
                    ip_text = scrapy.Selector(text = ip_text)
                    yield {
                        'ip': ip_text.xpath('//a/text()').extract_first(),
                        'port': int(tds[1].xpath('text()').extract_first()),
                        'https': tds[2].xpath('text()').extract_first()
                    }

        if not DEBUG:
            next_page = f'http://www.freeproxylists.net/?page={ProxyScrapSpider.page_number}'
            if ProxyScrapSpider.page_number <= ProxyScrapSpider.max_page:
                ProxyScrapSpider.page_number += 1
                yield response.follow(next_page, callback=self.parse)


def fetch():
    # core.proxy_fetchers.proxydashlistdownload.ProxyApiSpider
    spider = '.'.join([__name__, ProxyScrapSpider.__name__])
    data = os.popen(f'python {os.getcwd()}/core/proxy_fetchers/fetch.py {spider}').read()
    return  ast.literal_eval(data.strip())


if __name__ == '__main__':
    data = fetch()
    print(json.dumps(data, indent=4), f'count: {len(data)}')