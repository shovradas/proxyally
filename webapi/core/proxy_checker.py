# MIT License
# Copyright (c) 2020 Ricerati
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# Revised by: Shovra Das

import pycurl, random, json
from io import BytesIO

PROXY_JUDGES = [
    'http://proxyjudge.us/azenv.php',
    'http://mojeip.net.pl/asdfa/azenv.php',
    'https://azenv.net/',
    'http://www.proxy-listen.de/azenv.php',
    'http://httpheader.net/azenv.php'
]

IP_PROVIDERS = [
    'https://api.ipify.org/?format=json',
    'https://ip.seeip.org/jsonip',
    'https://api.myip.com/',
    'https://ip.seeip.org/jsonip',
    'https://api.my-ip.io/ip.json'
]

ANONYMOUS_HEADERS = [
    'ACCPROXYWS', 
    'CDN-SRC-IP', 
    'CLIENT-IP', #PREV
    'CLIENT_IP', 
    'CUDA_CLIIP', 
    'FORWARDED', #PREV
    'FORWARDED-FOR', #PREV
    'REMOTE-HOST', 
    'X-CLIENT-IP', 
    'X-COMING-FROM', 
    'X-FORWARDED', #PREV
    'X-FORWARDED-FOR', #PREV
    'X-FORWARDED-FOR-IP', #PREV
    'X-FORWARDED-HOST', 
    'X-FORWARDED-SERVER', 
    'X-HOST', 
    'X-NETWORK-INFO', 
    'X-NOKIA-REMOTESOCKET', 
    'X-PROXYUSER-IP', 
    'X-QIHOO-IP', 
    'X-REAL-IP', 
    'XCNOOL_FORWARDED_FOR', 
    'XCNOOL_REMOTE_ADDR'
]

ELITE_HEADERS = [
    'MT-PROXY-ID',
    'PROXY-AGENT',
    'PROXY-CONNECTION', #PREV
    'SURROGATE-CAPABILITY',
    'VIA', #PREV
    'X-ACCEPT-ENCODING',
    'X-ARR-LOG-ID',
    'X-AUTHENTICATED-USER',
    'X-BLUECOAT-VIA',
    'X-CACHE',
    'X-CID-HASH',
    'X-CONTENT-OPT',
    'X-D-FORWARDER',
    'X-FIKKER',
    'X-FORWARDED-PORT',
    'X-FORWARDED-PROTO',
    'X-IMFORWARDS',
    'X-LOOP-CONTROL',
    'X-MATO-PARAM',
    'X-NAI-ID',
    'X-NOKIA-GATEWAY-ID',
    'X-NOKIA-LOCALSOCKET',
    'X-ORIGINAL-URL',
    'X-PROXY-ID',
    'X-ROAMING',
    'X-TEAMSITE-PREREMAP',
    'X-TINYPROXY',
    'X-TURBOPAGE',
    'X-VARNISH',
    'X-VIA',
    'X-WAP-PROFILE',
    'X-WRPROXY-ID',
    'X-XFF-0',
    'XROXY-CONNECTION'
]

class HttpProxyChecker:
    def __init__(self, proxy_judges=None, ip_providers=None):
        self.proxy_judges = proxy_judges or PROXY_JUDGES
        self.ip_providers = ip_providers or IP_PROVIDERS
        self.ip = self.get_ip()

    def get_ip(self):
        resp = self.send_request(url=random.choice(self.ip_providers))
        ip = json.loads(resp)['ip']
        return ip

    def send_request(self, url, proxy=None):
        response = BytesIO()
        c = pycurl.Curl()

        c.setopt(c.URL, url)
        c.setopt(c.WRITEDATA, response)
        c.setopt(c.TIMEOUT, 5)

        c.setopt(c.SSL_VERIFYHOST, 0)
        c.setopt(c.SSL_VERIFYPEER, 0)

        if proxy:
            c.setopt(c.PROXY, proxy)

        # Perform request
        try:
            c.perform()
        except Exception as e:
            return False

        # Return False if the status is not 200
        if c.getinfo(c.HTTP_CODE) != 200:
            return False

        # Decoding the response content
        response = response.getvalue().decode('iso-8859-1')
        return response

    def determine_anonymity(self, judge_resp):
        if self.ip in judge_resp:
            return 'Transparent'
        
        privacy_headers = ANONYMOUS_HEADERS + ELITE_HEADERS
        if any([header in judge_resp for header in privacy_headers]):
            return 'Anonymous'

        #if any([header in judge_resp for header in ELITE_HEADERS]):
        return 'Elite'

    def check_proxy(self, proxy):
        judge_resp = self.send_request(url=random.choice(self.proxy_judges), proxy=f'http://{proxy}')
        if not judge_resp:
            return { 'status': 'offline'}
        
        return {
            'status': 'online', 
            'anonymity': self.determine_anonymity(judge_resp)
        }


if __name__ == '__main__':
    checker = HttpProxyChecker()
    result = checker.check_proxy('52.179.231.206:80')
    print(result)
    #result = checker.check_proxy('88.199.21.76:80')
    #print(result)
    #result = checker.check_proxy('87.199.21.76:80')
    #print(result)