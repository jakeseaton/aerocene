DEBUG = False

PRODUCTION_URL = ""

if DEBUG:
    PRODUCTION_URL = "http://localhost:5000"

# by default, scrape San Francisco
DEFAULT_LOCATION = 44961364

DEFAULT_CURSOR = ""

PAGE_SIZE = 50

# adversarial server settings
MAX_REQUESTS_PER_ADDRESS = 10