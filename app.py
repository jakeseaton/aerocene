import os
import boto3
import time
from flask import Flask, jsonify, request
import settings
from datetime import datetime
import time
import json
import random
import queries
import functions
import instagram

'''
This file implements a flask server
that is deployed as a single lambda function.
'''
app = Flask(__name__)

# index
@app.route("/")
def hello(*args, **kwargs):
    return jsonify({ "status": "live", "message": "Welcome to Aerocene!" })

# functions that implement Lisa's adversarial server
@app.route("/rate_limit")
def rate_limit(*args, **kwargs):
    # extract the ip address from the request
    address = request.remote_addr
    print("Address", address)

    # get or create a record for this address
    record = queries.get_or_create_address(address)['Item']

    # determine how many requests have been sent by this
    # address
    request_count = record.get("request_count")["N"]

    # if that's greater than the max we allow per address
    if int(request_count) >= settings.MAX_REQUESTS_PER_ADDRESS:

        # bye felicia
        return jsonify({
            "error": "429 Too Many Requests. Try again later."
        })

    # else increment the counter
    queries.increment_requests_for_address(address)

    # and return the updated record
    return jsonify(queries.get_address(address).get("Item"))


@app.route("/backoff")
def backoff(*args, **kwargs):

    address = request.remote_addr
    print("Address", address)

    record = queries.get_or_create_address(address).get("Item")

    request_count = int(record.get("request_count").get("N"))

    # if they've sent more requests than we allow per address
    if int(request_count) >= settings.MAX_REQUESTS_PER_ADDRESS:
        extra_requests = request_count - settings.MAX_REQUESTS_PER_ADDRESS
        # backoff exponentially
        time.sleep(2 ** extra_requests)


    queries.increment_requests_for_address(address)

    return jsonify(queries.get_address(address).get("Item"))


@app.route("/blacklist")
def blacklist(*args, **kwargs):
    address = request.remote_addr
    print("Address", address)

    record = queries.get_or_create_address(address).get("Item")

    request_count = int(record.get("request_count").get("N"))

    # if they've sent more requests than we allow per address
    if int(request_count) >= settings.MAX_REQUESTS_PER_ADDRESS:
        queries.blacklist_address(address)
        return jsonify({ "error": "403 Forbidden", "blacklisted": True })

    queries.increment_requests_for_address(address)
    return jsonify(queries.get_address(address).get("Item"))


def scrape_is_done(scrape_id):
    scrape = queries.get_scrape(scrape_id).get("Item")
    return scrape.get("progress").get("N") == scrape.get("end_page").get("N")


@app.route('/batch_scrape', methods=['GET'])
def batch_scrape(*args, **kwargs):

    location = request.args.get("location", 44961364)
    start_page = request.args.get("start_page", 0)
    end_page = request.args.get("end_page", 1)
    page_size = int(request.args.get("page_size", settings.PAGE_SIZE))
    scrape_id = queries.create_scrape(start_page, end_page, location, page_size)

    return jsonify({
        "status": "success",
        "message": "Batch scraping job was created successfully",
        "scrape_id": scrape_id,
        "location": location,
        "start_page": start_page,
        "end_page": end_page,
        "page_size": page_size,
    })


@app.route("/is_scrape_complete", methods=['GET'])
def is_scrape_complete(*args, **kwargs):
    scrape_id = request.args.get("scrape_id", "")

    if not scrape_id:
        return jsonify({"error": "You must specify a scrape_id to check"})

    return jsonify({
        "scrape_id": scrape_id,
        "is_complete": functions.check_if_scrape_is_complete(scrape_id)
    })


@app.route('/create_batch_scrape', methods=['POST'])
def batch_scrape_post(*args, **kwargs):
    location = request.form.get("location", 44961364)
    start_page = request.form.get("start_page", 0)
    end_page = request.form.get("end_page", 2)
    page_size = int(equest.form.get("page_size", settings.PAGE_SIZE))
    scrape_id = queries.create_scrape(start_page, end_page, location)
    return jsonify({"scrape_id": scrape_id})


# the main url we care about
@app.route('/scrape_instagram', methods=['GET'])
def scrape_instagram(*args, **kwargs):

    # get the location and cursor from the get parameters
    # of the request
    location = request.args.get('location', 44961364)
    cursor = request.args.get('cursor', '')
    page_size = int(request.args.get("page_size", settings.PAGE_SIZE))

    # if we didn't receive either one
    if not location and not cursor:
        # return an error
        return jsonify({'error': 'You must specify a location or an end cursor to scrape.'})

    result = instagram.scrape({'location': location, 'cursor': cursor}, {}, page_size)

    return jsonify(result)
