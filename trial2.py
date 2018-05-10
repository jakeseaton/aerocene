import requests
import json
import time
import settings
import sys


class Trial(object):
    pass

# otherwise use the result of the most recent run of `sls deploy`

# construct a template for generating new urls
BATCH_SCRAPE_URL = settings.PRODUCTION_URL + \
    "/batch_scrape?&location={0}&start_page={1}&end_page={2}&page_size={3}"

CHECK_UPDATE_URL = settings.PRODUCTION_URL + \
    "/is_scrape_complete?scrape_id={0}"


def scrape_is_complete(scrape_id):
    return json.loads(
        requests.get(
            CHECK_UPDATE_URL.format(scrape_id)
        ).content
    )['is_complete']


def batch_scrape(pages, page_size):
    print("Scraping %s pages of size %s using AWS lambda + dynamodb triggers" % (pages, page_size))
    t0 = time.time()
    batch_url = BATCH_SCRAPE_URL.format(settings.DEFAULT_LOCATION, 0, pages, page_size)
    print("Initializing scrape at", batch_url)
    response = requests.get(batch_url)

    scrape_id = json.loads(response.content)['scrape_id']

    while not scrape_is_complete(scrape_id):
        print("Checking in on scrape")
        time.sleep(1)

    t1 = time.time()
    print("Scraped %s pages in %s +- 1 second" % (pages, t1 - t0))


if __name__ == "__main__":
    try:
        pages = int(sys.argv[1])
        page_size = int(sys.argv[2])
    except:
        print("Usage: python trial2.py <pages:int> <page_size:int>")
        raise SystemExit

    if settings.DEBUG:
        print("Trial must be run on live deployment")
        print("Set DEBUG = False in settings.py and run `sls deploy --stage production`")
        print(
            "Then, update PRODUCTION_URL in settings.py with the url of the live deployment")
        raise SystemExit

    if not settings.PRODUCTION_URL:
        print("No PRODUCTION_URL set in settings.py")
        raise SystemExit

    batch_scrape(pages, page_size)