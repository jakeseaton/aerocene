from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random



def hello(event, context):
    ua = UserAgent(verify_ssl=False)
    proxies = []

    # Retrieve proxies.
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    #Save proxies in the list ip, port pair.
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })

    proxy_index = random.randint(0, len(proxies) - 1)
    proxy = proxies[proxy_index]

    final = ''
    #Test with icanhazip.com (returns proxied ip address)
    for n in range(1, 13):
        print("First request")
        req = Request('http://icanhazip.com')
        req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

        if n%10 == 0:
            proxy_index = random.randint(0, len(proxies) - 1)
            proxy = proxies[proxy_index]

        try:
            my_ip = urlopen(req).read().decode('utf8')
            #print("my_ip", my_ip)
            final = final + '#' + str(n) + ':' + my_ip
        except:
            del proxies[proxy_index]
            #print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
            proxy_index = random.randint(0, len(proxies) - 1)
            proxy = proxies[proxy_index]

    response = {
        "statusCode": 200,
        "body": final
    }
    #print(final)
    return response

#print(hello(None, None))
