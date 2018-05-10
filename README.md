# Aerocene
A distributed system for fault-tolerant web scraping

# GETTING STARTED

This is a fairly complext setup. It was developed using
OSX El-Capitan and python 3.

To run locally, you'll need DynamoDB installed on your machine: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html

To deploy it yourself, you'll need to install Docker, which requires creating a free account: https://docs.docker.com/install/

You'll also need to configure your AWS credentials.


Step 1: Create a Virtual Python Environment

- If you don't have a virtual environment wrapper installed, install `virtualenv`
- Create a virtual environment with Python 3
    virtualenv aerocene --python=python3;
    cd aerocene;
    source bin/activate;

Step 2: Clone the repo into the environment

git clone <repo_url> aerocene;
cd aerocene;

(Current directory /aerocene/aerocene/ )

Step 3: Install Depdendencies
- npm install -g serverless
- pip install -r requirements.txt
- npm install
- sls dynamodb install


Step 4: Run Development Mode
- Open settings.py and set DEBUG = True
- run `sls dynamodb start --migrate` to create a local dynamodb server
- open a new terminal and run `sls wsgi serve` to run the lambda server.
- Visit localhost:5000

Step 5: Run Trial 0 and Trial 1
- time python trial0.py <pages> <page_size>
- time python trial1.py <pages> <page_size>

Install the serverless framework

Setup serverless to work with AWS -- if you
don't have an AWS student account let me know.

clone the repo

cd aerocene

virtualenv aerocene --python=python3

source aerocene/bin/activate

pip install -r requirements.txt

sls swgi serve

(open new terminal)

python trial.py

To run dynamodb locally run sls dynamodb install (once you've added the plugin)

sls dynamodb start --migrate (you have to run it with this flag every time because=
out of the box it isn't saving the data, just storing it in memory. You can change this but
to do that you have to change some of this stuff
https://www.npmjs.com/package/serverless-dynamodb-local)

You need docker installed to deploy


If your stuff takes forever it's likely that the database isn't runnign
# Notes

We should be good on the AWS free tier as long
as we don't deloy too often. I used about 10% of the monthly limit on s3 PUT requests running `sls deploy`
while developing thus far.


# TODO

Tasks:
1 - Find and implement a better example than Instagram
    Linkedin? Pinterest? Something that doesn't intentionally
    slow down their API and responds within 6 seconds.
    Could also build our own API server.
    https://github.com/ericfourrier/scrape-linkedin

2 - Build a visualization
    - just set up a web page which allows you to type in a location
    and show both systems scraping stuff

3 - Optimize instagram implementation
    - Stop writing to ephemeral disk
    - Run trials with local



run lots of different trials in different environments

build a visualization

reduce space usage / having to write to ephemeral disk

build for other sites like linkedin or pinterest

Honestly we could also build an adversarial REST api
that does tricky rate limit things and then
build our system to get around it.


Rough estimates
AWS Lambda Free Tier
1M free requests
400k GB s free = 3.2M seconds

If you assume we use 100mb per s and each call takes 30s, that's 3 GBs
which gives us 100k free requests

at 100 images per request we get 10M free images.

This enables us to do 1000 trials of scraping 10,000 images each.


Use dynamo db locally?

# TODO
Do a test to figure out how often the ip changes. Write a lambda function that
just sends a request to a server or localhost and then deploy it and see how often it changes


Can we scrape just linkedin profile pictures?

Or senior photos on instagram somehow?


To run the trial make sure you have sls dynamodb start --migrate running locally