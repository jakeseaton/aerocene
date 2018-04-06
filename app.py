# app.py

import os

import boto3

from flask import Flask, jsonify, request
import settings
from datetime import datetime
import json
app = Flask(__name__)

USERS_TABLE = os.environ['USERS_TABLE']
INSTAGRAM_USERS_TABLE = os.environ['INSTAGRAM_USERS_TABLE']
INSTAGRAM_POST_TABLE = os.environ['INSTAGRAM_POST_TABLE']
INSTAGRAM_CURSOR_TABLE = os.environ['INSTAGRAM_CURSOR_TABLE']


# if we're running locally
if settings.DEBUG:
    # connect to the local instance of dynamo
    client = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-west-2')
else:
    # otherwise connect to the one in this cloud formation
    # TODO: figure out how this works and figures out where the db is
    client = boto3.client('dynamodb')

# index
@app.route("/")
def hello(*args, **kwargs):
    return "Welcome to Aerocene!"


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
    from functions import scrape_location_at_cursor

    # get the location and cursor from the get parameters
    # of the request
    location = request.args.get('location')
    cursor = request.args.get('cursor', '')

    # if we didn't receive either one
    if not location and not cursor:
        # return an error
        return jsonify({'error': 'You must specify a location or an end cursor to scrape.'})

    result = scrape_location_at_cursor(location, cursor)

    # we should use a batch insert for this!
    for post in result['data']:
        insert_post(post)

    insert_cursor(result['cursor'])

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

@app.route("/users/<string:user_id>")
def get_user(user_id):
    client = boto3.client('dynamodb')
    resp = client.get_item(
        TableName=USERS_TABLE,
        Key={
            'userId': { 'S': user_id }
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({'error': 'User does not exist'}), 404

    return jsonify({
        'userId': item.get('userId').get('S'),
        'name': item.get('name').get('S')
    })

@app.route("/instagram/<string:user_id>")
def get_instagram_user(user_id):
    print("This is the id", user_id)
    client = boto3.client('dynamodb')
    resp = client.get_item(
        TableName=INSTAGRAM_USERS_TABLE,
        Key={
            'id': {'S': user_id}
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({ 'error': 'User does not exist' }), 404

    return jsonify(item)

@app.route('/scrape/<string:location_id>')
def scrape_instagram_location(location_id):
    from functions import scrape_location
    return jsonify(scrape_location(location_id))


@app.route("/instagram", methods=["POST"])
def create_instagram_user():
    username = request.json.get('username')
    from functions import get_instagram_user
    user = get_instagram_user(username)
    import json
    client = boto3.client('dynamodb')
    resp = client.put_item(
        TableName=INSTAGRAM_USERS_TABLE,
        Item={
            'id': { 'S': user['id'] },
            'username': { 'S' : user['username'] },
            'user': {'S': json.dumps(user)}
        }
    )

    return jsonify({
        'id': user['id'],
        'username': user['username']
    })


@app.route("/users", methods=["POST"])
def create_user():
    user_id = request.json.get('userId')
    name = request.json.get('name')
    if not user_id or not name:
        return jsonify({'error': 'Please provider userId and name'}), 400
    client = boto3.client('dynamodb')
    resp = client.put_item(
        TableName=USERS_TABLE,
        Item={
            'userId': {'S': user_id },
            'name': {'S': name }
        }
    )

    return jsonify({
        'userId': user_id,
        'name': name
    })

def endpoint(event, context):
    current_time = datetime.datetime.now().time()
    body = {
        "message": "Hello, the current time is " + str(current_time)
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
