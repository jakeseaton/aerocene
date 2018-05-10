import requests
import json
import time
from settings import DEBUG

# are we debugging locally or running
# on the delopment instance

# scrape san francicso as the test case
location = 44961364

# the initial end cursor
cursor = ''


# otherwise use the result of the most recent run of `sls deploy`
base_url = "https://2k0ksl6gce.execute-api.us-east-1.amazonaws.com/production"

# construct a template for generating new urls
url_to_format = base_url + "/batch_scrape?&location={0}&start_page={1}&end_page={2}"


batch_scrape_url = base_url + "/batch_scrape"

check_update_url = base_url + "/is_scrape_complete?scrape_id={0}"

def scrape_is_complete(scrape_id):
    return json.loads(requests.get(check_update_url.format(scrape_id)).content)['is_complete']

def batch_scrape_one_page():
    t0 = time.time()
    response = requests.get(batch_scrape_url)

    scrape_id = json.loads(response.content)['scrape_id']


    while not scrape_is_complete(scrape_id):
        time.sleep(1)

    t1 = time.time()

    print("Scraped 1 page in %s seconds +- 1", t1 - t0)


def batch_scrape_100_pages():
    t0 = time.time()
    batch_url = url_to_format.format(location, 0, 100)
    scrape_id = json.loads(requests.get(batch_url).content)['scrape_id']

    while not scrape_is_complete(scrape_id):
        print("Checking in on scrape")
        time.sleep(1)

    t1 = time.time()
    print("Scraped 100 pages in %s +- 1 second", t1 - t0)
    # scrape_id = queries.create_scrape(0, 10, location)
    # print(scrape_id)
batch_scrape_100_pages()
# batch_scrape_one_page()
#     queries.create_scrape(start_page, end_page, location)
#     print("batch scraping")
#     data = {
#         "start_page": 0,
#         "end_page": 10,
#         "location": location
#     }
#     url = base_url + "/batch_scrape"
#     requests.post(url=url, data=data)


# batch_scrape()

# while not functions.check_if_scrape_is_complete(scrape_id):
#         print("Waiting on scrape", scrape_id)
#         time.sleep(1)

#     t1 = time.time()
#     return jsonify({
#         "start_page": start_page,
#         "end_page": end_page,
#         "total_time": t1 - t0,
#         "scrape_id": scrape_id,
#     })


