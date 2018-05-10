from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
from concurrent.futures import ThreadPoolExecutor
from instagram_web_api import Client, ClientCompatPatch

import time
import json
import boto3
import threading


def get_proxies():
    # Crates user agent.
    ua = UserAgent()
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
    return proxies

def create_proxy_dict(proxy):
    return {
        'http': 'http://%s:%s' % (proxy['ip'], proxy['port']),
        # 'https:': 'http://%s:%s' % (proxy['ip'], proxy['port'])
    }

def rotate_proxies(event, context):
    proxies = get_proxies()

    # Picking random proxy to use.
    proxy = random.choice(proxies)

    final = ''

    # Replace this with insta/dynamoDB scraping.
    # Tested with icanhazip.com API (returns proxied ip address).
    for n in range(0, 12):
        # Wait random time to send request.
        wait_time = random.uniform(0.1, 2.5)
        time.sleep(wait_time)

        # Request to icanhazip, which returns IP address that is used.
        req = Request('http://icanhazip.com')
        req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

        # Creating proxy url. Instantiating client.
        spoof = 'http://' + proxy['ip'] + ':' + proxy['port']
        web_api = Client(auto_patch=True, drop_incompat_keys=False, proxy=spoof, timeout=30)

        # To test if the client works...
        # token = web_api.csrftoken
        # print("Token", token)

        # Change the proxy ip/port combo every 2.
        if n%2 == 0:
            proxy_index = random.randint(0, len(proxies) - 1)
            proxy = proxies[proxy_index]

        try:
            my_ip = urlopen(req).read().decode('utf8')
            final = final + '#' + str(n) + ':' + my_ip
        except:
            del proxies[proxy_index]
            final = final + '# ' + 'failed'
            proxy_index = random.randint(0, len(proxies) - 1)
            proxy = proxies[proxy_index]

    # Test that rotation works.
    print(final)
    response = {
        "statusCode": 200,
        "body": final
    }
    return response

# Futures approach.
def cron_launcher(event, context):
    lambda_client = boto3.client('lambda', region_name="us-east-2")
    string_response = ''
    results = []
    futs = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        print("does this enter?")
        for x in range(0, 3):
            futs.append(
                executor.submit(rotate_proxies, None, None)
            )
        results = [fut.result() for fut in futs]
    print(len(results[0]))
    stuff = str(results[0])
    response = {
        "statusCode": 200,
        "body": stuff
    }
    return response


# print(cron_launcher(None, None))
