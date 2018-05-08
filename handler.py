from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random

import json
import boto3
import asyncio
import threading

# Rotates through proxy ips and sends requests to API. 
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

    # Picking random proxy to use.
    proxy_index = random.randint(0, len(proxies) - 1)
    proxy = proxies[proxy_index]

    final = ''

    # Replace this with insta/dynamoDB scraping.
    # Tested with icanhazip.com API (returns proxied ip address).
    for n in range(0, 15):
        console.log("request number: ", n)
        # Request to icanhazip, which returns IP address to be used.
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
            final = final + '# ' + 'failed'
            #print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
            proxy_index = random.randint(0, len(proxies) - 1)
            proxy = proxies[proxy_index]
    final += event
    response = {
        "statusCode": 200,
        "body": final
    }
    return response

# Main function.
def cron_launcher(event, context):
    lambda_client = boto3.client('lambda', region_name="us-east-2")
    string_response = ''

    lst = list(range(4))
    # Where the multithreading/concurrency should occur...
    # Use either threading, multiprocessing, or concurrent futures (if return type needed)
    # If note, InvocationType 'Event' is fine.
    for i in lst:
        t = threading.Thread(target=hello, args=(i,))
        lambda_client.invoke(FunctionName="aerocene-dev-hello", InvocationType='Event',
        Payload=json.dumps(str(i)))
        string_response += str(i)
        #string_response += response["Payload"].read().decode('utf-8')

    response = {
        "statusCode": 200,
        "body": string_response
    }
    return response
