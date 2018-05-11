import sys
import settings
import requests
import json


def scrape_endpoint(endpoint):
    print("Scraping the %s endpoint without ip rotation" % endpoint)
    timeout = 5
    counter = 0

    URL = settings.PRODUCTION_URL + "/" + endpoint
    CLEAR_URL = settings.PRODUCTION_URL + "/clear_address"
    print(URL)
    try:
        while True:
            print("Request", counter)
            response = requests.get(URL, timeout=timeout)
            status = json.loads(response.content).get("status", 200)

            if status == 429:
                raise ValueError("Rate Limited after %s requests" % counter)
            if status == 403:
                raise ValueError("Blacklisted after %s requests" % counter)
            counter += 1

    except requests.Timeout:
        print("Timed out after", counter, "requests")

    except Exception as e:
        print(e)

    requests.get(CLEAR_URL)


if __name__ == "__main__":
    try:
        endpoint = sys.argv[1]
        assert endpoint in ["backoff", "blacklist", "rate_limit"]
    except:
        import traceback; traceback.print_exc();
        print("Usage: python trial3.py <endpoint:backoff | blacklist | rate_limit>")
        raise SystemExit


    scrape_endpoint(endpoint)
