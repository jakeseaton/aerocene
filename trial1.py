import sys
import settings
import requests
import json
SCRAPE_URL = settings.PRODUCTION_URL + "/scrape_instagram?location={0}&cursor={1}&page_size={2}"

def lamdba_scrape(pages, page_size):
    print("Scraping %s pages of size %s using Lambda" % (pages, page_size))

    cursor = ""
    # records = set()
    # duplicates = 0
    for page in range(pages):
        scrape_url = SCRAPE_URL.format(settings.DEFAULT_LOCATION, cursor, page_size)
        print("Scraping page", page, scrape_url)
        response = json.loads(requests.get(scrape_url).content)
        cursor = response['cursor']
        # for record in response['data']:
        #     if record['id'] in records:
        #         duplicates += 1
        #     else:
        #         records.add(record['id'])
        # print("Duplicates found", duplicates)


if __name__ == "__main__":
    print("Scrapes instagram using lambda functions in the cloud")
    try:
        pages = int(sys.argv[1])
        page_size = int(sys.argv[2])
    except:
        print("Usage: python trial1.py <pages:int> <page_size:int>")
        raise SystemExit

    if not settings.PRODUCTION_URL:
        print("No PRODUCTION_URL set in settings.py")
        raise SystemExit

    lamdba_scrape(pages, page_size)