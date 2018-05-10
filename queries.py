
import boto3
import settings
import os
import datetime

# if we're running locally
if settings.DEBUG:
    # connect to the local instance of dynamo
    client = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-west-2')
    lambda_client = boto3.client("lambda", endpoint_url="http://localhost:4000", region_name='us-west-2')
else:
    # otherwise connect to the one in this cloud formation
    # TODO: figure out how this works and figures out where the db is
    client = boto3.client('dynamodb')

INSTAGRAM_POST_TABLE = os.environ['INSTAGRAM_POST_TABLE']
INSTAGRAM_CURSOR_TABLE = os.environ['INSTAGRAM_CURSOR_TABLE']
SCRAPE_TABLE = os.environ['SCRAPE_TABLE']
REQUEST_TABLE = os.environ['REQUEST_TABLE']


def get_address(address):
    return client.get_item(
        TableName=REQUEST_TABLE,
        Key={
            'address': { 'S': address }
        }
    )

def get_or_create_address(address):

    if get_address(address).get("Item", {}):
        return get_address(address)

    client.put_item(
        TableName=REQUEST_TABLE,
        Item={
            'address': { 'S': address },
            'request_count': {'N': str(0)},
            'blacklisted': {'BOOL': False}
        },
        ReturnValues="ALL_OLD"
    )

    return get_address(address)

def blacklist_address(address):
    return client.update_item(
        TableName=REQUEST_TABLE,
        Key={ 'address': {'S': address} },
        UpdateExpression= 'SET blacklisted = :new',
        ExpressionAttributeValues={":new": {'BOOL': True}},
        ReturnValues="ALL_OLD"
    )


def increment_requests_for_address(address):
    return client.update_item(
        TableName=REQUEST_TABLE,
        Key={ 'address': {'S': address} },
        UpdateExpression= 'SET request_count = request_count + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )


def generate_unique_scrape_id():
    # this is the worst possible way to do this
    return client.describe_table(TableName=SCRAPE_TABLE)["Table"]["ItemCount"] + 1

def create_scrape(start_page, end_page, location):
    scrape_id = generate_unique_scrape_id()
    client.put_item(
        TableName=SCRAPE_TABLE,
        Item={
            'id': { 'N': str(scrape_id)},
            'start_page': { 'N': str(start_page) },
            'end_page': { 'N': str(end_page) },
            'progress': { 'N': str(0) },
            'location': { 'S': str(location) },
            # you can't have empty strings in dynamodb which is
            # laaaame
            # 'cursor': { 'S': '' },
        }
    )
    return scrape_id

def get_scrape(scrape_id):
    return client.get_item(
        TableName=SCRAPE_TABLE,
        Key={ 'id': {'N': str(scrape_id)} },
    )

def increment_scrape_progress(scrape_id):
    print("Incrementing progress for scrape with id", scrape_id)
    return client.update_item(
        TableName=SCRAPE_TABLE,
        Key={ 'id': {'N': str(scrape_id)} },
        UpdateExpression= 'SET progress = progress + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )

def increment_progress_and_cursor(scrape_id, cursor):
    print("Updating progress for scrape with id", scrape_id, "New Cursor", cursor)
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
        Key={ 'id': {'N': str(scrape_id)} },
        UpdateExpression= 'SET progress = :new',
        ConditionExpression="progress = :old",
        ExpressionAttributeValues = {
            ":old": {"N": str(old_progress)},
            ":new": {"N": str(new_progress)}
        },
        ReturnValues="UPDATED_NEW"
    )

def insert_cursor(cursor, location):
    return client.put_item(
        TableName=INSTAGRAM_CURSOR_TABLE,
        Item={
            'cursor': { 'S': cursor },
            'created': { 'S': str(datetime.datetime.now()) },
            'scraped': { 'BOOL': False },
            'location': { 'S': str(location) }
        }
    )

def insert_posts(posts):
    for post in posts:
        # print("This is a post")
        pass

def get_cursor(cursor):
    return client.get_item(
        TableName=INSTAGRAM_CURSOR_TABLE,
        Key={
            'cursor': { 'S': cursor }
        }
    )

def insert_post(post):
    resp = client.put_item(
        TableName=INSTAGRAM_POST_TABLE,
        Item={
            'id': { 'S': post['id'] },
            'data': {'S': json.dumps(post)}
        },
    )