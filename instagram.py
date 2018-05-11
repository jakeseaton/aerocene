from instagram_web_api import Client
import settings
import proxy

'''
This file interfaces between Aerocene and the
instagram_web_api library for sending queries
to Instagram. It defines a single function,
scrape, a lambda function
that tages a location and a cursor and executes a
scrape at that location and cursor.
'''

def scrape(event, context, page_size=settings.PAGE_SIZE):

    # Instagram no longer enables scraping of pages
    # larger than 50. We want to enable scraping pages of
    # different sizes for trial purposes, but if
    # we try it with more than 50 Instagram will just block
    # the request
    assert page_size <= 50, "Page size must be <= 50"

    # extract the location and cursor from the arguments.
    # We use "event" and "context" in accordance with the Lambda
    # convention.
    location_id = event.get('location', settings.DEFAULT_LOCATION)
    end_cursor = event.get('cursor', None)

    # instantiate the instagram web client
    web_api = Client(auto_patch=True, drop_incompat_keys=False)

    # query a page of this location's feed
    location_feed_info = web_api.location_feed(
        location_id,
        count=page_size,
        end_cursor=end_cursor,
        proxy=proxy.get_random_http_proxy()
    )

    if location_feed_info['status'] != "ok":
        raise

    # massage the GraphQL response into a more usable form
    location = location_feed_info['data']['location']
    media = location['edge_location_to_media']

    # top_posts = location['edge_location_to_top_posts']

    del location['edge_location_to_media']
    del location['edge_location_to_top_posts']

    cursor = media['page_info']['end_cursor']
    # has_next_page = media['page_info']['has_next_page']

    posts = [node['node'] for node in media['edges']]

    # return the response
    return {
        "cursor": cursor,
        "data": posts,
    }