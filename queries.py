import boto3
import settings
import os
import json

###
# This modules contains
# functions that performs
# queries on dynamodb
###

# first, establish a connection to the correct dynamodb.
# It is important to do this outside of the functions
# because then the connection will be maintained
# by the docker container instead of having
# to open and close a new one each
# time we call a function

if settings.DEBUG:
    print("Connecting to local dynamodb...")
    client = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-west-2'
    )
else:
    print("Connecting to production dynamodb...")
    # otherwise connect to the one in this cloud formation
    try:
        client = boto3.client('dynamodb')
    except Exception as e:
        # if that fails, it could be
        # a misconfigured setttings file
        print("Failed to connect to dynamodb.")
        print("If you're running locally set DEBUG = True in settings.py")
        raise SystemExit

# extract the names of the DynamoDB tables that we
# defined in serverless.yml from the environment variables
INSTAGRAM_POST_TABLE = os.environ['INSTAGRAM_POST_TABLE']
SCRAPE_TABLE = os.environ['SCRAPE_TABLE']
REQUEST_TABLE = os.environ['REQUEST_TABLE']

###
# ScrapeDynamoDBTable Queries:
# Queries for interacting with the table
# containing scraping jobs
##

# trivial mechanism for generating unique ids for
# scraping jobs
def generate_unique_scrape_id():
    # this is the worst possible way to do this for a variety of reasons but is fine for our
    # design scope.
    return client.describe_table(TableName=SCRAPE_TABLE)["Table"]["ItemCount"] + 1

    # some of those reasons are that the describe_table function does not guarantee accuracy,
    # and that monotonically increasing integers aren't necessarily unique across shards. For our
    # design case we aren't worried about sharding the DynamoDB tables.

# create a record for a scraping job defined by its start and end pages, the
# location we're sraping, and how many items to scrape on each page
def create_scrape(start_page, end_page, location=settings.DEFAULT_LOCATION, page_size=settings.PAGE_SIZE):
    # create a unique id for this job
    scrape_id = generate_unique_scrape_id()
    # insert it into the database
    client.put_item(
        TableName=SCRAPE_TABLE,
        Item={
            'id': {'N': str(scrape_id)},
            'start_page': {'N': str(start_page)},
            'end_page': {'N': str(end_page)},
            'progress': {'N': str(0)},
            'location': {'S': str(location)},
            'page_size': {'N': str(page_size)},
            # you can't have empty strings in dynamodb which is
            # laaaame
            # 'cursor': { 'S': '' },
        }
    )
    # return the unique id
    return scrape_id

# query the scrape represented by a particular id
def get_scrape(scrape_id):
    return client.get_item(
        TableName=SCRAPE_TABLE,
        Key={'id': {'N': str(scrape_id)}},
    )

# increment the progress of a particular
# scrape by 1
def increment_scrape_progress(scrape_id):
    print("Incrementing progress for scrape with id", scrape_id)
    return client.update_item(
        TableName=SCRAPE_TABLE,
        Key={'id': {'N': str(scrape_id)}},
        UpdateExpression='SET progress = progress + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )

# increment the progress of a particular scrape
# and update its cursor
def increment_progress_and_cursor(scrape_id, cursor):
    print("Updating progress for scrape with id",
          scrape_id, "New Cursor", cursor)
    return client.update_item(
        TableName=SCRAPE_TABLE,
        Key={'id': {'N': str(scrape_id)}},
        UpdateExpression="SET progress=progress + :num, end_cursor = :end_cursor",
        ExpressionAttributeValues={
            ":num": {"N": "1"},
            ":end_cursor": {"S": str(cursor)}
        },
        ReturnValues="UPDATED_NEW",
    )

# update the progress of a particular scrape on the condition
# that it is currently in the state described by old_progress
def update_scrape_progress(scrape_id, old_progress, new_progress):
    print("Setting scrape with id", scrape_id, "to progress", new_progress)
    return client.update_item(
        TableName=SCRAPE_TABLE,
        Key={'id': {'N': str(scrape_id)}},
        UpdateExpression='SET progress = :new',
        ConditionExpression="progress = :old",
        ExpressionAttributeValues={
            ":old": {"N": str(old_progress)},
            ":new": {"N": str(new_progress)}
        },
        ReturnValues="UPDATED_NEW"
    )

###
# InstagramPostDynamoDB Queries:
# queries for interacting with
# the table containing scraped instagram
# posts.
###
#
def insert_posts(posts):
    # perform a batch insert into
    # the instagram post table
    for post in posts:
        insert_post(post)


def insert_post(post):
    return client.put_item(
        TableName=INSTAGRAM_POST_TABLE,
        Item={
            'id': {'S': post['id']},
            'data': {'S': json.dumps(post)}
        },
    )


###
# RequestDynamoDBTable Queries:
# Queries for interacting with the table
# containing ip addresses of inbound requests
# for use by the adversarial server.
###

# the the record representing requests
# sent from a single ip address
def get_address(address):
    return client.get_item(
        TableName=REQUEST_TABLE,
        Key={
            'address': {'S': address}
        }
    )

# get the record representing
# requests sent from a single ip address,
# or if it doesn't exist yet, create it
# and then return it.
def get_or_create_address(address):

    if get_address(address).get("Item", {}):
        return get_address(address)

    client.put_item(
        TableName=REQUEST_TABLE,
        Item={
            'address': {'S': address},
            'request_count': {'N': str(0)},
            'blacklisted': {'BOOL': False}
        },
        ReturnValues="ALL_OLD"
    )

    # the put_item function doesn't return the
    # whole item so we have to do a third query here.
    return get_address(address)

# update the record for an ip address
# to set it as blacklisted
def blacklist_address(address):
    return client.update_item(
        TableName=REQUEST_TABLE,
        Key={'address': {'S': address}},
        UpdateExpression='SET blacklisted = :new',
        ExpressionAttributeValues={":new": {'BOOL': True}},
        ReturnValues="ALL_OLD"
    )



# updates the record for an ip address to increase the
# requests we've seen by 1
def increment_requests_for_address(address):
    return client.update_item(
        TableName=REQUEST_TABLE,
        Key={'address': {'S': address}},
        UpdateExpression='SET request_count = request_count + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )

# reset the count of requests seen from a particular address
def reset_requests_for_address(address):
    return client.update_item(
        Key={'address': {'S': address}},
        UpdateExpression='SET request_count = :num',
        ExpressionAttributeValues={":num": {"N": "0"}},
        ReturnValues="UPDATED_NEW"
    )

# deletes the record of a given address,
# effectively clearing it.
def delete_address(address):
    return client.delete_item(
        TableName=REQUEST_TABLE,
        Key={'address': {'S': address}}
    )
