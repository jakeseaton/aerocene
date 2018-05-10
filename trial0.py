import sys
import settings
import instagram

def scrape_locally(pages, page_size=settings.PAGE_SIZE):
    print("Scraping %s pages of size %s locally" % (pages, page_size))
    # records = set()
    # duplicates = 0
    cursor = None
    for page in range(pages):
        print("Scraping page", page)
        # duplicates = 0
        event = { 'cursor': cursor }
        response = instagram.scrape(event, {}, page_size)
        cursor = response['cursor']
        # for record in response['data']:
        #     if record['id'] in records:
        #         duplicates += 1
        #     else:
        #         records.add(record['id'])
        # print("Duplicates found", duplicates)



if __name__ == "__main__":
    try:
        pages = int(sys.argv[1])
        page_size = int(sys.argv[2])
    except:
        import traceback; traceback.print_exc();
        print("Usage: python trial0.py <pages:int> <page_size:int>")
        raise SystemExit

    scrape_locally(pages, page_size)