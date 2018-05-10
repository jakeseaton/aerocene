# app.py

import os

import boto3

from flask import Flask, jsonify, request
import settings
from datetime import datetime
import json
app = Flask(__name__)

INSTAGRAM_POST_TABLE = os.environ['INSTAGRAM_POST_TABLE']
INSTAGRAM_CURSOR_TABLE = os.environ['INSTAGRAM_CURSOR_TABLE']
SCRAPE_TABLE = os.environ['SCRAPE_TABLE']

DEBUG = settings.DEBUG

# if we're running locally
if DEBUG:
    # connect to the local instance of dynamo
    client = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-west-2')
    lambda_client = boto3.client("lambda", endpoint_url="http://localhost:4000", region_name='us-west-2')
else:
    # otherwise connect to the one in this cloud formation
    # TODO: figure out how this works and figures out where the db is
    client = boto3.client('dynamodb')

# index
@app.route("/")
def hello(*args, **kwargs):
    return "Welcome to Aerocene!"



def generate_unique_scrape_id():

    # this is the worst possible way to do this
    return client.describe_table(TableName=SCRAPE_TABLE)["Table"]["ItemCount"] + 1

    # could alternatively use the instagram implementation

def schmerp(*args, **kwargs):
    starting_item_count = client.describe_table(TableName=SCRAPE_TABLE)["Table"]["ItemCount"]

    print("Starting item count", starting_item_count)
    # this is one of the worst ways I can possible think of to generate a unique id for scrapes
    unique_id = generate_unique_scrape_id()
    # inserting record
    client.put_item(
        TableName=SCRAPE_TABLE,
        Item={
            'id': { 'N': str(unique_id)},
            'start_page': { 'N': str(0) },
            'end_page': { 'N': str(10) },
            'progress': { 'N': str(0) },
        }
    )

    new_item_count = client.describe_table(TableName=SCRAPE_TABLE)["Table"]["ItemCount"]
    print("New Item count", new_item_count)


    # assert(increment_progress(unique_id)['Attributes']['progress']['N'] == '1')
    # assert(update_record(unique_id, 0, 1)['Attributes'] == [])
    # assert(update_record(unique_id, 1, 2)['Attributes']['progress']['N'] == '2')

    return {}

def increment_scrape_progress(scrape_id):
    print("Incrementing progress for scrape with id", scrape_id)
    response = client.update_item(
        TableName=SCRAPE_TABLE,
        Key={ 'id': {'N': str(scrape_id)} },
        UpdateExpression= 'SET progress = progress + :num',
        ExpressionAttributeValues={":num": {"N": "1"}},
        ReturnValues="UPDATED_NEW"
    )
    return response

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


@app.route('/batch_scrape', methods=['POST'])
def batch_scrape(*args, **kwargs):
    print(args, kwargs)
    print(request.form)
    start_page = request.form.get("start_page", 0)
    end_page = request.form.get("end_page", 1)

    print(client.describe_table(TableName=INSTAGRAM_CURSOR_TABLE))

    # resp = client.put_item(
    #     TableName=INSTAGRAM_POST_TABLE,
    #     Item={
    #         'id': { 'S': post['id'] },
    #         'data': {'S': json.dumps(post)}
    #     },
    # )
    print("Starting on page", start_page)
    print("Ending on page", end_page)

    # maybe store the function name as well
    # lambda_client.invoke(
    #     FunctionName="derp",
    #     InvocationType="RequestResponse",
    #     Payload=json.dumps({ 'start_page': start_page, 'end_page': end_page })
    # )

    return jsonify({ 'success': True })




@app.route('/list_tables', methods=['GET'])
def list_tables(*args, **kwargs):
    print(client.list_tables())
    return jsonify({'success': True})

def insert_cursor(cursor):
    resp = client.put_item(
        TableName=INSTAGRAM_CURSOR_TABLE,
        Item={
            'cursor': { 'S': cursor },
            'created': { 'S': str(datetime.now()) }
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

# the main url we care about
@app.route('/scrape_instagram', methods=['GET'])
def scrape_instagram(*args, **kwargs):
    from functions import scrape_instagram_web

    # get the location and cursor from the get parameters
    # of the request
    location = request.args.get('location')
    cursor = request.args.get('cursor', '')

    # if we didn't receive either one
    if not location and not cursor:
        # return an error
        return jsonify({'error': 'You must specify a location or an end cursor to scrape.'})

    result = scrape_instagram_web({ 'location': location, 'cursor': cursor}, {})

    # print("The returned cursor was", result['cursor'])

    # result = scrape_location_at_cursor(location, cursor)

    # insert the cursor object to trigger the next round of scraping
    insert_cursor(result['cursor'])

    # we should use a batch insert for this!
    # for post in result['data']:
    #     insert_post(post)

    # scrape this location at this cursor
    return jsonify(result)




@app.route("/posts", methods=["POST"])
def posts():
    username = request.json.get("username")
    if not username:
        return jsonify({'error': 'Please provide a username'}), 400
    return jsonify({
        'username': username,
        'posts': [],
    })

