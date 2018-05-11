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

The @app.route decorators map functions to
urls, so that when you run `sls wsgi serve`
You can go to localhost/<function> to
exectute that function
'''

app = Flask(__name__)

# index route
@app.route("/")
def hello(*args, **kwargs):
    '''
    Indicates that this Aerocene build is live
    '''
    return jsonify({ "status": 200, "message": "Welcome to Aerocene!" })

###
# Adversarial Server
# - exposes endpoints that emulate canonical methods of preventing scraping
# - rate limiting
# - blacklisting
# - exponential backoff
###
@app.route("/rate_limit")
def rate_limit(*args, **kwargs):
    '''
    Limit the number of inbound requests to a certain
    amount per day.
    '''

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
            "status": 429,
            "error": "Too Many Requests. Try again later."
        })

    # else increment the counter
    queries.increment_requests_for_address(address)

    # and return the updated record
    return jsonify(queries.get_address(address).get("Item"))


@app.route("/backoff")
def backoff(*args, **kwargs):
    '''
    Implements exponential backoff by ip address.
    After the maximum number of requests from
    a particular address have been seen, sleeps
    for an exponentially increasing amount of time
    before returning
    '''
    address = request.remote_addr
    print("BACKOFF Address", address)

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
    '''
    Implements blacklisting
    After the maximum number of requests
    from a particular address have been seen,
    mark the address as banned and never
    respond to it again.
    '''
    address = request.remote_addr
    print("Address", address)

    record = queries.get_or_create_address(address).get("Item")

    request_count = int(record.get("request_count").get("N"))

    # if they've sent more requests than we allow per address
    if int(request_count) >= settings.MAX_REQUESTS_PER_ADDRESS or record.get("blacklisted").get("BOOL"):
        queries.blacklist_address(address)
        return jsonify({ "status": 403, "error": "Forbidden", "blacklisted": True })

    queries.increment_requests_for_address(address)
    return jsonify(queries.get_address(address).get("Item"))

@app.route("/clear_address")
def clear_address(*args, **kwargs):
    '''
    For testing purposes, expose an endpoint
    to clear the record of a client's ip address
    '''

    address = request.remote_addr

    print("Clearing address", address)
    try:
        queries.delete_address(address)
        return jsonify({ "status": 200, "message": "Successfully cleared %s" % address })

    except Exception as e:
        return jsonify({ "status": 500, "error": e })



###
# Bacth scraping mechanism. Enables a client
# to create scraping jobs.
###
@app.route('/batch_scrape', methods=['GET'])
def batch_scrape(*args, **kwargs):
    '''
    Endpoint for initializing batch scrapes.
    When called, creates a record in dynamodby
    that causes the CloudFormation to begin scraping
    and updating that record.
    '''

    # extract arguments from query parameters on the url
    location = request.args.get("location", settings.DEFAULT_LOCATION)
    start_page = request.args.get("start_page", 0)
    end_page = request.args.get("end_page", 1)
    page_size = int(request.args.get("page_size", settings.PAGE_SIZE))

    # create the scrape record
    scrape_id = queries.create_scrape(start_page, end_page, location, page_size)

    # return a json response that describes the created record
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
    '''
    Endpoint a waiting machine can query to determine if a scrape they initiated
    has finished yet.
    Queries the scrape in question, checks if it is done, and returns
    a json continaing the result as a boolean.
    '''

    # extract scrape id from query parameters
    scrape_id = request.args.get("scrape_id", "")

    # handle error
    if not scrape_id:
        return jsonify({"error": "You must specify a scrape_id to check"})

    # check if done and return a response
    return jsonify({
        "scrape_id": scrape_id,
        "is_complete": functions.check_if_scrape_is_complete(scrape_id)
    })


@app.route('/create_batch_scrape', methods=['POST'])
def batch_scrape_post(*args, **kwargs):
    '''
    POST request implementation of batch_scrape
    '''
    location = request.form.get("location", settings.DEFAULT_LOCATION)
    start_page = request.form.get("start_page", 0)
    end_page = request.form.get("end_page", 2)
    page_size = int(equest.form.get("page_size", settings.PAGE_SIZE))
    scrape_id = queries.create_scrape(start_page, end_page, location)
    return jsonify({"scrape_id": scrape_id})

###
# Scraping functionality.
###
@app.route('/scrape_instagram', methods=['GET'])
def scrape_instagram(*args, **kwargs):
    '''
    Endpoint that can be queried to manually scrape instagram
    at a particular location and cursor.
    '''

    # get the location and cursor from the get parameters
    # of the request
    location = request.args.get('location', settings.DEFAULT_LOCATION)
    cursor = request.args.get('cursor', '')
    page_size = int(request.args.get("page_size", settings.PAGE_SIZE))

    # if we didn't receive either one
    if not location and not cursor:
        # return an error
        return jsonify({'error': 'You must specify a location or an end cursor to scrape.'})

    # use the instagram module to scrape on those parameters
    # and return the result
    result = instagram.scrape({'location': location, 'cursor': cursor}, {}, page_size)

    return jsonify(result)
