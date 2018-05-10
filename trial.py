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
DEBUG = False

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

# send ten requests per trial
for i in range(0, 100):
    try:
        # initialize the number of repeated posts to zero
        repeats = 0

        # timestamp
        # print("Request number %s at cursor %s" % (i, cursor))


        # format the url
        url = url_to_format.format(location, cursor)

        # send the request
        # print("Sending request to %s" % url)
        t01 = time.time()
        try:
            response = requests.get(url)
            data = json.loads(response.text)
        except Exception as e:
            print(e)
            errors += 1
            continue
        t02 = time.time()

        # extract the cursor and data from the result

        cursor = data['cursor']
        records = data['data']

        # print("Received %s at cursor %s" % (len(records), cursor))

        # timestamp


        time_to_scrape = t02 - t01
        times.append(time_to_scrape)

        # print("Scraped %s records in %s seconds." % (len(records), t02 - t01))

        # check for duplicates
        for record in records:
            if record['id'] in record_ids:
                repeats += 1
            else:
                record_ids.add(record['id'])
        print("Request %s repeated records %s" % (i, repeats))

        # continue
    except:
        import traceback; traceback.print_exc();
        raise SystemExit
if errors:
    print("Total errors: %s" % errors)
print("Total Network Time: %s" % sum(times))
print("Average time per request %s" % (sum(times) / len(times)))