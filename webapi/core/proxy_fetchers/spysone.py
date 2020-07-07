import scrapy, os, json, re
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url
import ast
from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyScrapSpider(scrapy.Spider):
    name = 'spysone'

    def start_requests(self):
        if DEBUG:
            url = urljoin('file:', pathname2url(f'{os.getcwd()}/core/proxy_fetchers/providers_offline/spysone.html'))
            yield scrapy.Request(url, self.parse_table)
        else:
            yield scrapy.Request('http://spys.one/en/http-proxy-list/', self.parse)

    def parse(self, response):
        xx0 = response.xpath('//input[@name="xx0"]/@value').extract_first()
        yield response.follow(response.url, method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'}, body='xx0={xx0}&xpp=5&xf1=0&xf2=0&xf4=0&xf5=0', callback=self.parse_table)

    def parse_table(self, response):
        var_string = response.xpath('//script')[3].xpath('text()').extract_first()
        trs = response.xpath('//tr[@onmouseover]')
        for tr in trs:
            tds = tr.xpath('td')
            yield {
                'ip': tds[0].xpath('font/text()').extract_first().strip(),
                'port': self.compute_port(var_string, tds[0].xpath('font/script/text()').extract_first().strip())
                #'code': tds[2].xpath('text()').extract_first(),
                #'country': tds[3].xpath('text()').extract_first(),
                #'anonymity': tds[4].xpath('text()').extract_first().strip(' proxy'),
                #'https': tds[6].xpath('text()').extract_first()
            }

    def compute_port(self, var_string, port_string):
        #print(var_string, port_string)
        #var_string = 'a1j0 = 4123; r8c3 = 3681; m3y5 = 1365; u1z6 = 9255; e5r8 = 6480; f6d4 = 2848; k1h8 = 3982; w3x4 = 7594; o5e5 = 5703; p6p6 = 5228; b2q7h8 = 0 ^ a1j0; a1d4f6 = 1 ^ r8c3; p6v2b2 = 2 ^ m3y5; q7m3w3 = 3 ^ u1z6; s9f6c3 = 4 ^ e5r8; z6p6e5 = 5 ^ f6d4; c3c3r8 = 6 ^ k1h8; o5i9m3 = 7 ^ w3x4; j0y5x4 = 8 ^ o5e5; d4g7v2 = 9 ^ p6p6;'
        var_string = var_string.replace(' ', '')
        var_string = var_string.split(';')[:-1]
        var_string = [re.sub(r'\^.*', '', x) for x in var_string]
        vars = { kv.split('=')[0].strip():int(kv.split('=')[1]) for kv in var_string}

        #port_string = 'document.write("<font class=spy2>:<\/font>" + (j0y5x4 ^ o5e5) + (b2q7h8 ^ a1j0) + (j0y5x4 ^ o5e5) + (b2q7h8 ^ a1j0))'
        port_string = port_string.split('+')[1:]
        port_string = [re.sub(r'\^.*', '', x)[1:].strip() for x in port_string]
        port_string = [x.replace('(', '') for x in port_string]
        port_string = [str(vars[x]) for x in port_string]
        port = ''.join(port_string)
        
        return int(port)


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