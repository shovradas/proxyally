import scrapy, os, json, re
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyScrapSpider(scrapy.Spider):
    name = 'proxynovacom'
    max_page=3

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/proxynovacom.html'))
            yield scrapy.Request(url, self.parse_table)
        else:
            yield scrapy.Request('https://www.proxynova.com', self.parse)

    def parse(self, response):
        urls = response.xpath('//ul/li/a[contains(@href, "/proxy-server-list/country-")]/@href').extract()
        abs_urls = []
        for url in urls:
            abs_urls.append(response.urljoin(url))
        yield from response.follow_all(abs_urls[:ProxyScrapSpider.max_page], callback=self.parse_table)

    def parse_table(self, response):
        trs = response.xpath('//tr[@data-proxy-id]')
        for tr in trs:
            tds = tr.xpath('td')
            ip_text = tds[0].xpath('abbr/script/text()').extract_first()
            yield {
                'ip': re.search("'.*'", ip_text).group(),
                'port': int(tds[1].xpath('text()').extract_first().strip())      
            }


def fetch():
    # core.proxy_fetchers.proxydashlistdownload.ProxyApiSpider
    spider = '.'.join([__name__, ProxyScrapSpider.__name__])
    data = os.popen(f'python {os.getcwd()}/core/proxy_fetchers/fetch.py {spider}').read()
    return  ast.literal_eval(data)


if __name__ == '__main__':
    data = fetch()
    print(json.dumps(data, indent=4), f'count: {len(data)}')