import json
from constants import *
import requests
import os
quit = False

def much_better_scrape(event, context):
    location_id = event.get('location', "212988663")
    end_cursor = event.get('cursor', None)
    '''
    Uses the instagram_private_api thingy to scrape
    instagram without having to log in
    '''
    from instagram_web_api import Client, ClientCompatPatch

    web_api = Client(auto_patch=True, drop_incompat_keys=False)

    location_feed_info = web_api.location_feed(location_id, count=50, cursor=end_cursor)

    if location_feed_info['status'] == "ok":
        pass

    # print(location_feed_info)
    # open("herp.json", "w").write(json.dumps(location_feed_info))

    location = location_feed_info['data']['location']

    media = location['edge_location_to_media']
    top_posts = location['edge_location_to_top_posts']

    del location['edge_location_to_media']
    del location['edge_location_to_top_posts']

    cursor = media['page_info']['end_cursor']
    has_next_page = media['page_info']['has_next_page']

    posts = [node['node'] for node in media['edges']]
    return {
        "cursor": cursor,
        "data": posts,
    }


# scrapes ten records from the passed location
# id at the given index
def scrape_location_at_cursor(location, cursor):
    # import the main function from our
    # custom version of the instagram scraper library
    from instagram_scraper.app import main
    import sys

    # set the argumetns we want to
    # pass to the parser
    args = [
        "instagram-scraper",
        "%s" % location,
        "--location",
        "--media-metadata",
        "--maximum=10",
        "--media-types=none",
        "-u=fashion.amplify",
        "-p=sfg]cfR(HMrZxyB2kgTj"
    ]

    # if we have a cursor to start at,
    # ass that as an argument
    if cursor:
        args.append("--cursor=%s" % cursor)

    # set these arguments to be argv
    sys.argv = args

    # execute the scraper
    main()

    # the scraper will write
    # its results to ephemeral disk
    # space "/tmp/", where we
    # can retrieve the results

    # This is not ideal -- I just did this
    # to save time avoiding re-writing all of the
    # logic to scrape instagram

    # open the json file containing the metadata we wanted
    d = json.loads(open("/tmp/%s/%s.json" % (location, location), "r").read())

    # open the text file containing the cursor to
    # continue scraping at
    c = open("/tmp/cursor.txt", "r").read()

    # return the dictionary of these
    # two items
    return {
        "cursor": c,
        "data": d,
    }

def hello(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response


# retrieves the record representing an instagram user
def get_user_response(username):
    url = USER_URL.format(username)
    resp = get_json(url)
    if resp:
        return resp
    raise

# deletes the un-needed fields from a user
# record to save space in DynamoDB
def store_user(user):
    # we don't care about their posts
    del user['edge_owner_to_timeline_media']
    del user['edge_saved_media']
    del user['edge_media_collections']
    # store the user in the database
    # TODO

# gets and returns the record from
# user with the given username
def get_instagram_user(username, *args, **kwargs):
    response = get_user_response(username)
    user = json.loads(response)['graphql']['user']
    # if user and user['is_private'] and user['edge_owner_to_timeline_media']['count'] > 0 and not user['edge_owner_to_timeline_media']['edges']:
    #     self.logger.error('User {0} is private'.format(username))
    return user

# gets the post of an instagram user with the
# passed username
def get_user_posts(username, *args, **kwargs):
    print("Username", username)

    user = get_instagram_user(username)

    open("data/%s.json" % username, "w").write(json.dumps(user))

    media = user['edge_owner_to_timeline_media']

    posts = []
    if not media['count']:
        return posts

    posts += media['edges']

    if media['page_info']['has_next_page']:
        end_curos = media['page_info']['end_cursor']

    print("currently have", len(posts), "of", media['count'], "media")

    return username

# returns the json
def get_json(*args, **kwargs):
    resp = safe_get(*args, **kwargs)
    if resp is not None:
        return resp.text



def sleep(secs):
    min_delay = 1
    for _ in range(secs // min_delay):
        time.sleep(min_delay)
        if quit:
            return
    time.sleep(secs % min_delay)

# helper function stolen from
# instagram-scraper to perform get requests
def safe_get(*args, **kwargs):
    # stolen from
    # out of the box solution
    # session.mount('https://', HTTPAdapter(max_retries=...))
    # only covers failed DNS lookups, socket connections and connection timeouts
    # It doesnt work when server terminate connection while response is downloaded
    session = requests.Session()
    session.headers = {'user-agent': CHROME_WIN_UA}
    retry = 0
    retry_delay = RETRY_DELAY
    while True:
        if quit:
            return
        try:
            response = session.get(timeout=CONNECT_TIMEOUT, *args, **kwargs)
            if response.status_code == 404:
                return
            response.raise_for_status()
            content_length = response.headers.get('Content-Length')
            if content_length is None or len(response.content) != int(content_length):
                #if content_length is None we repeat anyway to get size and be confident
                raise PartialContentException('Partial response')
            return response
        except (KeyboardInterrupt):
            raise
        except (requests.exceptions.RequestException, PartialContentException) as e:
            if 'url' in kwargs:
                url = kwargs['url']
            elif len(args) > 0:
                url = args[0]
            if retry < MAX_RETRIES:
                # self.logger.warning('Retry after exception {0} on {1}'.format(repr(e), url))
                sleep(retry_delay)
                retry_delay = min( 2 * retry_delay, MAX_RETRY_DELAY )
                retry = retry + 1
                continue
            # else:
            #     keep_trying = self._retry_prompt(url, repr(e))
            #     if keep_trying == True:
            #         retry = 0
            #         continue
            #     elif keep_trying == False:
            #         return
            raise

