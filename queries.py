import boto3
import settings
import os
import json

'''
This file contains
functions that performs
queries on dynamodb
'''

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
        print("Failed to connect to dynamodb.")
        print("If you're running locally set DEBUG = False in settings.py")
        raise SystemExit

INSTAGRAM_POST_TABLE = os.environ['INSTAGRAM_POST_TABLE']
SCRAPE_TABLE = os.environ['SCRAPE_TABLE']
REQUEST_TABLE = os.environ['REQUEST_TABLE']


def get_address(address):
    return client.get_item(
        TableName=REQUEST_TABLE,
        Key={
            'address': {'S': address}
        }
    )


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

    return get_address(address)


def blacklist_address(address):
    return client.update_item(
        TableName=REQUEST_TABLE,
        Key={'address': {'S': address}},
        UpdateExpression='SET blacklisted = :new',
        ExpressionAttributeValues={":new": {'BOOL': True}},
        ReturnValues="ALL_OLD"
    )


def increment_requests_for_address(address):
    return client.update_item(
        TableName=REQUEST_TABLE,
        Key={'address': {'S': address}},
        UpdateExpression='SET request_count = request_count + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )


def reset_requests_for_address(address):
    return client.update_item(
        Key={'address': {'S': address}},
        UpdateExpression='SET request_count = :num',
        ExpressionAttributeValues={":num": {"N": "0"}},
        ReturnValues="UPDATED_NEW"
    )


def generate_unique_scrape_id():
    # this is the worst possible way to do this
    return client.describe_table(TableName=SCRAPE_TABLE)["Table"]["ItemCount"] + 1


def create_scrape(start_page, end_page, location=settings.DEFAULT_LOCATION, page_size=settings.PAGE_SIZE):
    scrape_id = generate_unique_scrape_id()
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
    return scrape_id


def get_scrape(scrape_id):
    return client.get_item(
        TableName=SCRAPE_TABLE,
        Key={'id': {'N': str(scrape_id)}},
    )


def increment_scrape_progress(scrape_id):
    print("Incrementing progress for scrape with id", scrape_id)
    return client.update_item(
        TableName=SCRAPE_TABLE,
        Key={'id': {'N': str(scrape_id)}},
        UpdateExpression='SET progress = progress + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )


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
