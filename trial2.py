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


# if we're testing locally
if DEBUG:
    # use localhost
    base_url = "http://localhost:5000"
else:
    # otherwise use the result of the most recent run of `sls deploy`
    base_url = "https://3g8hkjrfr0.execute-api.us-east-1.amazonaws.com/dev"

# construct a template for generating new urls
url_to_format = base_url + "/scrape_instagram?&location={0}&cursor={1}"

# initialize a set of scraped post ids
record_ids = set()

times = list()

errors = 0

def batch_scrape():
    print("batch scraping")
    data = {
        "start_page": 0,
        "end_page": 10,
        "location": location
    }
    url = base_url + "/batch_scrape"
    requests.post(url=url, data=data)


batch_scrape()