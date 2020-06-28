import scrapy, os, json
from urllib.parse import unquote, urljoin
from urllib.request import pathname2url

from config import DEBUG

# DEBUG=False

# custom spider having the parse logic
class ProxyScrapSpider(scrapy.Spider):
    name = 'dw'

    def start_requests(self):
        yield scrapy.Request('https://www.dw.com/de/themen/s-9077', self.parse)

    def parse(self, response):
        #divs = response.xpath('//div[@class="news"]')
        #print(divs)
        
        #for div in divs:
        #    yield {
        #        'link': response.urljoin(div.xpath('a/@href').extract_first().strip()),
        #        'title': div.xpath('a/h2/text()').extract_first().strip(),
        #        'img': response.urljoin(div.xpath('a/div/img/@src').extract_first().strip()),
        #        'summary': div.xpath('a/p/text()').extract_first().strip()
        #    }

        col = response.xpath('//div[@class="col2 left"]')
        
        category = ''
        for div in col.xpath('div'):
            div_class = div.xpath('@class').extract_first()
            if(div_class == "subHeader subHeaderTeaser"):
                category = div.xpath('text()').extract_first().strip()
                continue
            else:
                news_div = div.xpath('div')
                if news_div.xpath('a'):
                    yield { #//*[@id="bodyContent"]/div[2]/div[11]/div/a/div[2]/h2
                        'category': category,
                        'link': response.urljoin(news_div.xpath('a/@href').extract_first().strip()),
                        'title': news_div.xpath('a/div[2]/h2/text()').extract_first().strip(),
                        'img': response.urljoin(news_div.xpath('a/div[1]/img/@src').extract_first().strip()),
                        'summary': news_div.xpath('a/div[2]/p/text()').extract_first().strip()
                    }
                else:                    
                    yield {
                        'category': category,
                        'link': response.urljoin(news_div.xpath('div/a/@href').extract_first().strip()),
                        'title': news_div.xpath('div/a/h2/text()').extract_first().strip(),
                        'img': response.urljoin(news_div.xpath('div/a/div/img/@src').extract_first()),
                        'summary': news_div.xpath('div/a/p/text()').extract_first().strip()
                    }

def fetch():
    return scrapy_helper.crawl(ProxyScrapSpider)    


if __name__ == '__main__':
    data = fetch()
    print(json.dumps(data, indent=4), f'count: {len(data)}')
    with open('D:\dw.json', 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)
        print('file written: D:\dw.json')