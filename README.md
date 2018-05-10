# Aerocene
A CloudFormation for distributed, fault-tolerant web scraping.

# Directory Structure

# Set Up

Warning: This setup process is highly complex and has a lot of moving pieces.

To run Aerocene locally, you'll need DynamoDB installed: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html

To deploy an Aerocene CloudFormation to AWS, you'll need to [install Docker](https://docs.docker.com/install/), which requires creating a free account. You'll also need to configure your AWS credentials.


## Step 1: Create a Virtual Python Environment

- If you don't have a virtual environment wrapper installed, install `virtualenv`
- Create a virtual environment with Python 3


    `virtualenv aerocene --python=python3;`

    `cd aerocene;`

    `source bin/activate;`

## Step 2: Clone the repo into the environment

` git clone <repo_url> aerocene;`

`cd aerocene;`

(Current directory `/aerocene/aerocene/` )


## Step 3: Install Depdendencies

You'll need both the python requirements and the javascript requirements for Serverless. The python requirements can be installed via pip, and the javascript via npm.

Install the serverless framework globally (to be able to use the CLI)

`npm install -g serverless`

Log in to serverless, configure AWS credentials

`sls login`

Install python requirements

`pip install -r requirements.txt`

Install javascript dependencies

`npm install`

Install dynamodb plugin for serverless

`sls dynamodb install`


## Step 4: Run Aerocene Development Mode

- Open settings.py and set DEBUG = True

- run `sls dynamodb start --migrate` to create a local dynamodb server

- open a new terminal and run `sls wsgi serve` to run the lambda server.

- Open a browser to `http://localhost:5000`. You should receive a successful response.

- Navigate to `http://localhost:5000/scrape_instagram`. You should receive a json response containing Instagram.

## Step 5: Run trials locally

Trial 0 scrapes Instagram by sending requests from your machine. Start with 10 pages of size 10.

`time python trial0.py <pages> <page_size>`

Trial 1 (in development mode) scrapes instagram by sending requests through the locally running Aerocene.

`time python trial1.py <pages> <page_size>`

Trial 2 does not work in development mode.

## Step 5: Deploy Production build

Note -- this won't work if you don't have an AWS account and your credentials set up, or aren't logged in to serverless.

Open settings.py and change `DEBUG = False`.

Use serverless to deploy to AWS

`sls deploy --stage production`

It should take a couple of minutes

