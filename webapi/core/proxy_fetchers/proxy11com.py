import scrapy, os, json
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

##################
#
# Sign in required, have to check api trial period
#
##################

# DEBUG=False

# custom spider having the parse logic
class ProxyApiSpider(scrapy.Spider):
    name = 'proxy11com'

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/proxy11com.json'))
            yield scrapy.Request(url, self.parse)
        else:
            yield scrapy.Request('https://proxy11.com/api/proxy.json?key=MTM4Nw.XulXOg.pbVkEpugepwbpwSQ09binLAz_Sk', self.parse)

    def parse(self, response):
        items = json.loads(response.body)
        for item in items['data']:            
            yield {
                'ip': item['ip'],
                'port': int(item['port'])
            }


def fetch(config):
    ProxyApiSpider.custom_settings = {
        'DOWNLOAD_DELAY': config['downloadDelay']
    }
    # core.proxy_fetchers.proxydashlistdownload.ProxyApiSpider
    spider = '.'.join([__name__, ProxyApiSpider.__name__])
    data = os.popen(f'python {os.getcwd()}/core/proxy_fetchers/fetch.py {spider}').read()
    return  ast.literal_eval(data)


if __name__ == '__main__':
    data = fetch()
    print(json.dumps(data, indent=4), f'count: {len(data)}')