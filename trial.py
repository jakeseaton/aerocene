import requests
import json
import time

# are we debugging locally or running
# on the delopment instance
DEBUG = True

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
    base_url = "https://kv5r3g2u1b.execute-api.us-east-1.amazonaws.com/dev"

# construct a template for generating new urls
url_to_format = base_url + "/scrape_instagram?&location={0}&cursor={1}"

# initialize a set of scraped post ids
record_ids = set()

# send ten requests per trial
for i in range(0, 10):
    try:
        # initialzie the number of repeated posts to zero
        repeats = 0

        # timestamp
        print("Request number %s at cursor %s" % (i, cursor))
        t01 = time.time()

        # format the url
        url = url_to_format.format(location, cursor)

        # send the request
        print("Sending request to %s" % url)
        response = requests.get(url)
        data = json.loads(response.text)

        # extract the cursor and data from the result
        cursor = data['cursor']
        records = data['data']

        # timestamp
        t02 = time.time()
        print("Scraped %s records in %s seconds." % (len(records), t02 - t01))

        # check for duplicates
        for record in records:
            if record['id'] in record_ids:
                repeats += 1
            else:
                record_ids.add(record['id'])
        print("Repeated records %s" % repeats)

        # continue
    except:
        import traceback; traceback.print_exc();
        raise SystemExit