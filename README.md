# aerocene

At this point I've built a proof of concept that it's
possible to scrape Instagram usign AWS Lambda.

It's pretty ugly and I'm not sure that it's faster
than doing it with a single server.

I've rewritten the "instagram-scraper" library to
use /tmp/ files and return the necessary cursor variable
so that we don't have to reinvent the whlle of scraping it
ourselves.

In particular I bet that scraping 100 records at a time
locally is much faster and cheaper than having a lambda function
scrape 10 at at time.

I thought it was just my computer being gradually throttled
but it seems that the instagram api is just incredibly slow on
purpose to disable scraping.

# GETTING STARTED
Clone the repository

make a virtual environment
virtualenv <name> --python=python3

activate virtual environment
source <name>/bin/activate

install requiremenst
pip install -r requirements.txt

install npm dependencies
npm install

try to run the server
sls wsgi serve

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