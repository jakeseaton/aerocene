import json
from constants import *
import requests
import os

def hello(event, context):
    # print("YOOOO")
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response


def get_user_response(username):
    url = USER_URL.format(username)
    resp = get_json(url)
    if resp:
        return resp
    raise

def store_user(user):
    # we don't care about their posts
    del user['edge_owner_to_timeline_media']
    del user['edge_saved_media']
    del user['edge_media_collections']
    # store the user in the database

def get_instagram_user(username, *args, **kwargs):
    response = get_user_response(username)
    user = json.loads(response)['graphql']['user']

    # if user and user['is_private'] and user['edge_owner_to_timeline_media']['count'] > 0 and not user['edge_owner_to_timeline_media']['edges']:
    #     self.logger.error('User {0} is private'.format(username))

    return user

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

def get_json(*args, **kwargs):
    resp = safe_get(*args, **kwargs)
    if resp is not None:
        return resp.text

quit = False

def sleep(secs):
    min_delay = 1
    for _ in range(secs // min_delay):
        time.sleep(min_delay)
        if quit:
            return
    time.sleep(secs % min_delay)


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
def scrape_location(location, *args, **kwargs):
    os.system('instagram-scraper --location %s --media-metadata --maximum=100 --media-types none' % location)
    d = json.loads(open("%s/%s.json" % (location, location), "r").read())
    c = open("cursor.txt", "r").read()
    return {
        "cursor": c,
        "data": d
    }

