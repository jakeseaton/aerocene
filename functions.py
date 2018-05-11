import json
import requests
import os
import instagram
import queries

'''
This file contains lambda handlers and their helper functions.
'''

# helper function to extract the cursor
# value from a dynamodb record
def extract_cursor(scrape):
    # handle the case where a cursor has not been set yet
    # (One eccenetricity of DynamoDB is that it does not
    # allow empty strings, so the property will not exist)
    return scrape.get("end_cursor", {'S': ''})['S']


# introspects on a scrape record to
# determine if it is complete or not
def scrape_is_complete(scrape):
    end_page = scrape['end_page']['N']
    progress = scrape['progress']['N']
    return progress == end_page or int(progress) > int(end_page)


# queries a scraping job and returns
# whether or not it is complete
def check_if_scrape_is_complete(scrape_id):
    scrape = queries.get_scrape(scrape_id).get("Item")
    return scrape_is_complete(scrape)


# given the record representing a
# scraping job, perform a scrape
# of the next page
def scrape_next_page(scrape):
    import queries
    scrape_id = scrape['id']['N']
    location = scrape['location']['S']
    page_size = scrape['page_size']['N']

    # use our helper to extract the cursor
    # in case it does not exist yet
    cursor = extract_cursor(scrape)

    # if we're done with this scrape
    if scrape_is_complete(scrape):
        # do nothing
        return

    # use the instagram module to perform the scrape at this cursor
    response = instagram.scrape({'location': location, 'cursor': cursor}, {}, int(page_size))

    # extract the new cursor from the response
    new_cursor = response['cursor']

    # increment the progress of this scrape and set
    # its new cursor, so that another function can handle
    # the rest of the scrape
    queries.increment_progress_and_cursor(scrape_id, new_cursor)

    # insert the posts returned by this scrxape
    queries.insert_posts(response['data'])

###
# Stream Handlers -- triggered
# by DynamoDB streams.
###
def scrape_stream_handler(event, context):
    '''
    Process CloudWatch events in thhe ScrapeDynamoDbTable
    stream. Events are of the form
        {
            "Records": [
                {
                    "eventName": <string>
                    "dynamodb": <ScrapeRecord>
                },
                {}...
            ]
        }
    '''
    # print(event)
    for record in event.get("Records", []):
        if record['eventName'] == "INSERT":
            scrape = record['dynamodb']['NewImage']
            scrape_next_page(scrape)

        if record['eventName'] == "MODIFY":
            old_image = record['dynamodb']['OldImage']
            new_image = record['dynamodb']['NewImage']
            # if the cursors are different
            if extract_cursor(new_image) != extract_cursor(old_image):
                scrape_next_page(new_image)
            # otherwise this is probably just a progress update
    return {}

