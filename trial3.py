import sys
import settings
import requests
import json

RATE_LIMIT_URL = settings.PRODUCTION_URL + "/rate_limit"
BLACKLIST_URL = settings.PRODUCTION_URL + "/blacklist"
BACKOFF_URL = settings.PRODUCTION_URL + "/backoff"

def scrape_blacklist():
    response = requests.get(BLACKLIST_URL)
    counter = 1
    while json.loads(response.content).get("status", 200) != 403:
        print("Request", counter)
        response = requests.get(BLACKLIST_URL)
        counter += 1
        print(json.loads(response.content))

    print("Blacklisted after", counter, "requests")


def scrape_rate_limit():
    response = requests.get(RATE_LIMIT_URL)
    counter = 1
    while json.loads(response.content).get("status", 200) != 429:
        print("Request", counter)
        response = requests.get(RATE_LIMIT_URL)
        counter += 1
    print("Rate limited after", counter, "requests")


def scrape_backoff():
    timeout = 5
    counter = 0
    try:
        while True:
            print("Request", counter)
            response = requests.get(BACKOFF_URL, timeout=timeout)
            counter += 1
    except requests.Timeout:
        print("Timed out after", counter, "requests")

if __name__ == "__main__":
    # try:
    #     pages = int(sys.argv[1])
    #     page_size = int(sys.argv[2])
    # except:
    #     import traceback; traceback.print_exc();
    #     print("Usage: python trial0.py <pages:int> <page_size:int>")
    #     raise SystemExit

    scrape_backoff()
