import scrapy, os, json
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyApiSpider(scrapy.Spider):
    name = 'proxydashlistdownload'
    #custom_settings = {
    #    'DOWNLOAD_DELAY': 1
    #}

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/proxydashlistdownload.txt'))
            yield scrapy.Request(url, self.parse)
        else:
            yield scrapy.Request('https://www.proxy-list.download/api/v1/get?type=http', self.parse)
            yield scrapy.Request('https://www.proxy-list.download/api/v1/get?type=https', self.parse)

    def parse(self, response):
        content = response.body.decode('utf-8').split('\r\n')[:-1]
        for line in content:
            line = line.split(':')
            yield {
                'ip': line[0],
                'port': int(line[1])
            }


def fetch(config):
    ProxyApiSpider.custom_settings = {
        'DOWNLOAD_DELAY': config['downloadDelay']
    }
    # core.proxy_fetchers.proxydashlistdownload.ProxyApiSpider
    spider = '.'.join([__name__, ProxyApiSpider.__name__])
    data = os.popen(f'python {os.getcwd()}/core/proxy_fetchers/fetch.py {spider}').read()
    with open('D:/proxy.txt', 'w') as fp:
        json.dump(ProxyApiSpider.custom_settings, fp)

    return ast.literal_eval(data)


if __name__ == '__main__':
    data = fetch()    
    print(json.dumps(data), f'count: {len(data)}')
