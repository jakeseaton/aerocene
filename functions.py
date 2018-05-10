import json
import requests
import os
from instagram_web_api import Client, ClientCompatPatch
import queries

def derp(*args, **kwargs):
    scrape_id = queries.create_scrape(0,1,1234)
    queries.increment_progress_and_cursor(scrape_id, "asdf")
    return queries.get_scrape(scrape_id)

def trial(event, context):
    location = 44961364
    queries.create_scrape(0, 10, location)
    print("Yo waddup")
    return {}

def get_cursor(scrape):
    return scrape.get("end_cursor", {'S': ''})['S']

def scrape_is_complete(scrape):
    end_page = scrape['end_page']['N']
    progress = scrape['progress']['N']
    return progress == end_page or int(progress) > int(end_page)

def check_if_scrape_is_complete(scrape_id):
    scrape = queries.get_scrape(scrape_id).get("Item")
    return scrape_is_complete(scrape)


def scrape_next_page(scrape):
    import queries
    scrape_id = scrape['id']['N']
    location = scrape['location']['S']

    # this has to be nasty because
    # the attribute might not exist
    # and no empty strings are allowed in
    # dynamodb
    cursor = get_cursor(scrape)

    # if we're done with this scrape
    if scrape_is_complete(scrape):
        # do nothing
        return

    response = scrape_instagram_web({ 'location': location, 'cursor': cursor }, {})

    new_cursor = response['cursor']

    # increment the progress of this scrape and set
    # its new cursor, so that another function can handle
    # the rest of the scrape
    queries.increment_progress_and_cursor(scrape_id, new_cursor)

    # insert the responses of this
    queries.insert_posts(response['data'])


def cursor_stream_handler(event, context):
    # print(event)
    records = event.get("Records", [])
    for record in records:
        if record['eventName'] == "INSERT":
            # extract the new cursor from the event
            new_cursor = record['dynamodb']['NewImage']
            cursor = new_cursor['cursor']['S']
            location = new_cursor['location']['S']


    return event
            # invoke a different lambda function
            # lambda_invoke(scrape_cursor(...))

def scrape_stream_handler(event, context):
    # print(event)
    for record in event.get("Records", []):
        if record['eventName'] == "INSERT":
            scrape = record['dynamodb']['NewImage']
            scrape_next_page(scrape)

        if record['eventName'] == "MODIFY":
            old_image = record['dynamodb']['OldImage']
            new_image = record['dynamodb']['NewImage']
            # if the cursors are different
            if get_cursor(new_image) != get_cursor(old_image):
                scrape_next_page(new_image)
            # otherwise this is probably just a progress update
    return {}


def herp(event, context):
    records = event.get("Records", [])
    print(records)
    # assert(len(records) == 1, "Too many records %s" % records)
    for record in records:
        if record['eventName'] == "INSERT":
            new_cursor = record['dynamodb']

            return new_cursor['NewImage']['cursor']['S']


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