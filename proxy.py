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

###
# This module includes functions for
# performing ip rotation. It queries a
# website that lists a set of
# proxies available for public use,
# and then formats them for use
# by the python requests module
###

# query proxies from sslproxies.org
def get_proxies():

    # Create user agent.
    ua = UserAgent()

    # Retrieve proxies.
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    # use beautiful soup to parse proxies from
    # html
    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # return an array of proxies of the form
    # { ip: <address: string>, port: <port: string> }
    return [
        {
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        }
        for row
        in proxies_table.tbody.find_all('tr')
    ]

# when this file is executed,
# query the proxies so that
# we don' thave to make this request
# repeatedly
proxies = get_proxies()

# convert the dictionary representation of the
# proxy to one with the https keys
def create_proxy_dict(proxy):
    return {
        'https': 'https://%s:%s' % (proxy['ip'], proxy['port']),
        # 'https:': 'http://%s:%s' % (proxy['ip'], proxy['port'])
    }

# returns a random proxy of the form { https: proxy }
def get_random_proxy_dict():
    return create_proxy_dict(random.choice(proxies))

# returns a random proxy as an http url
def get_random_http_proxy():
    p = random.choice(proxies)
    return 'http://' + p['ip'] + ':' + p['port']

# lambda function to test rotation
# of proxies
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
        web_api = Client(
            auto_patch=True, drop_incompat_keys=False, proxy=spoof, timeout=30)

        # To test if the client works...
        # token = web_api.csrftoken
        # print("Token", token)

        # Change the proxy ip/port combo every 2.
        if n % 2 == 0:
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
