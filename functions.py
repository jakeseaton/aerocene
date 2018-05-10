import json
import requests
import os
from instagram_web_api import Client, ClientCompatPatch

def cursor_stream_handler(event, context):
    records = event.get("Records", [])
    for record in records:
        if record['eventName'] == "INSERT":
            # extract the new cursor from the event
            new_cursor = record['dynamodb']['NewImage']['cursor']['S']
    return event
            # invoke a different lambda function
            # lambda_invoke(scrape_cursor(...))

def scrape_stream_handler(event, context):
    for e in event.get("Records", []):
        if record['eventName'] == "INSERT":
            new_scrape = record['dynamodb']['NewImage']['id']['N']
            print(new_scrape)
    return new_scrape


def herp(event, context):
    records = event.get("Records", [])
    print(records)
    # assert(len(records) == 1, "Too many records %s" % records)
    for record in records:
        if record['eventName'] == "INSERT":
            new_cursor = record['dynamodb']

            return new_cursor['NewImage']['cursor']['S']

def derp(event, context):
    print("Derp!", event, context)
    return event


def scrape_instagram_web(event, context):
    location_id = event.get('location', "212988663")
    end_cursor = event.get('cursor', None)

    # print("Sending request to cursor", end_cursor)
    '''
    Uses the instagram_private_api thingy to scrape
    instagram without having to log in
    '''

    web_api = Client(auto_patch=True, drop_incompat_keys=False)

    location_feed_info = web_api.location_feed(location_id, count=10, end_cursor=end_cursor)

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
    # print("Returning cursor", cursor)
    return {
        "cursor": cursor,
        "data": posts,
    }