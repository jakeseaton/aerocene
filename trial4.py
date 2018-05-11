import sys
import settings
import requests
import json
import proxy
import random
from urllib.request import Request, urlopen


def scrape_endpoint(endpoint):

    timeout = 5
    counter = 0
    proxies = proxy.get_proxies()


    URL = settings.PRODUCTION_URL + "/" + endpoint
    CLEAR_URL = settings.PRODUCTION_URL + "/clear_address"
    print("Scraping the %s endpoint with ip rotation: %s " % (endpoint, URL))

    try:
        while True:
            print("Request", counter)

            curr_proxy = proxy.create_proxy_dict(random.choice(proxies))
            print("Proxy: ", curr_proxy)
            response = requests.get(URL, proxies=curr_proxy)
            status = json.loads(response.content).get("status", 200)

            if status == 429:
                raise ValueError("Rate Limited after %s requests" % counter)
            if status == 403:
                raise ValueError("Blacklisted after %s requests" % counter)
            counter += 1

    except requests.Timeout:
        print("Timed out after", counter, "requests")

    except Exception as e:
        import traceback; traceback.print_exc();
        print(e)

    requests.get(CLEAR_URL)

if __name__ == "__main__":
    try:
        endpoint = sys.argv[1]
        assert endpoint in ["backoff", "blacklist", "rate_limit"]
    except:
        import traceback; traceback.print_exc();
        print("Usage: python trial4.py <endpoint:backoff | blacklist | rate_limit>")
        raise SystemExit

    if settings.DEBUG:
        print("Trial4 must be run on production instance for proxies to work")

    scrape_endpoint(endpoint)
