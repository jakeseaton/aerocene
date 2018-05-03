import json
import requests
import os
from instagram_web_api import Client, ClientCompatPatch

def scrape_instagram_web(event, context):
    location_id = event.get('location', "212988663")
    end_cursor = event.get('cursor', None)
    '''
    Uses the instagram_private_api thingy to scrape
    instagram without having to log in
    '''


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