DEBUG = True

PRODUCTION_URL = "https://ozh5lhpa2k.execute-api.us-east-2.amazonaws.com/production"

if DEBUG:
    PRODUCTION_URL = "http://localhost:5000"

# by default, scrape San Francisco
DEFAULT_LOCATION = 44961364

DEFAULT_CURSOR = ""

PAGE_SIZE = 50

# adversarial server settings
MAX_REQUESTS_PER_ADDRESS = 10