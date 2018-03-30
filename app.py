# app.py

import os

import boto3

from flask import Flask, jsonify, request
app = Flask(__name__)

USERS_TABLE = os.environ['USERS_TABLE']
INSTAGRAM_USERS_TABLE = os.environ['INSTAGRAM_USERS_TABLE']
client = boto3.client('dynamodb')

@app.route("/")
def hello():
    return "Hello World!"


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


@app.route("/instagram", methods=["POST"])
def create_instagram_user():
    username = request.json.get('username')
    from functions import get_instagram_user
    user = get_instagram_user(username)
    import json
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
