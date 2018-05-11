
# Aerocene
### Serverless Scraping

# Abstract

We’ve designed and built a distributed system that uses 'serverless' technology to execute web scraping tasks. The system is deployed as an AWS CloudFormation composed of Lambda, DynamoDB, and APIGateway. It uses the [serverless framework](https://serverless.com/). By submitting a single request to the Aerocene CloudFormation, the user can create a DynamoDB record of a scraping job to be performed. The system will then automatically distribute all the necessary requests through Lambda functions. While the system failed to improve the time complexity of scraping as we had hoped, it substantially reduces the overhead necessary to develop and deploy scraping applications, and successfully circumvents complex mechanisms for pagination, rate-limiting, blacklisting and otherwise preventing programatic access to internet content.

# Introduction

Web scraping is a pain. Programs that automate the process of checking for updates to websites enable the creation of incredibly valuable data and powerful software--from legal documents to social media content, recipes to job listings. Unfortunately, without a massive army of dedicated servers, a smaller army of dedicated engineers, and a sophisticated protocol for distributing jobs amongst both, it proves extremely difficult to scrape in a fault-tolerant fashion at scale. Every website is structured differently, and employs different countermeasures to data collection that change without warning. This means that you not only have to write different code for each website you want to scrape, but constantly check those websites to make sure that their structure or various countermeasures haven't changed.

The relatively recent advent of 'serverless' technology, a regrettable misnomer for products such as AWS Lambda and Google Cloud Functions, presents an opportunity to design systems that by nature circumvent some of the biggest challenges to web scraping. The definition of a function can be uploaded to the cloud service provider of choice, and without needing a dedicated server instance the function can be executed at arbitrary scale. These properties align with the ideal web scraper in several ways. Some things web scraping engineers have to worry about are:

- Creating entirely new servers every time their ip address gets blacklisted
- Rotating requests between ip addresses to avoid rate limits
- One request out of hundreds failing or timing out and crashing the entire program
- Resources wasted waiting on requests
- Crashing a server by starting too many threads or processes
- Proliferation of zombie processes that result from any of the above

Meanwhile, 'serverless' technology proposes:

- Built in ip-rotation as function invocations occur at arbitrary locations in the cloud
- Arbitrary scalability and removing the need to think in terms of servers
- Isolated invocations that prevent a single failure from effecting other processes
- Rapid development and deployment without needing complex build scripts and crontabs
- Event-driven invocation triggers such as DynamoDB streams
- Low cost pay-as-you-go compute resources with millions of free invocations per month

This means that 'serverless' designs will by nature resolve some of the largest headache of building web scrapers, and even reduce their price tag in terms of devlopment hours and cloud resources.

The objective of this project was the build an interesting distributed system for performing web scraping tasks using serverless technology. Our hypothesis was that a serverless model would be cheaper, faster to build, and naturally circumvent some of the larger pain points of web scraping development such as rate limiting and blacklisting. We were optimistic that parallelizing across cloud functions might result in a performance boost.

At the time this project began, Instagram was among the most highly coveted data by web scrapers. Instagram's API and website made content posted on public profiles readily available to those with a system capable of ingesting the firehose of images and information posted there on a daily basis. Entire companies such as [Trendalytics](https://www.trendalytics.co/), [Influenster](https://www.influenster.com/) and  [Heuritech](https://www.heuritech.com/) have built businesses based on processing the image and textual data of instagram and packaging it for the fashion industry. This incredibly rich, publicly available dataset was therefore the ideal initial target for our scraping strategies.

Shortly after beginning the project, the Cambridge Analytica scandal broke, and Instagram and Facebook severely restricted developer access to their Api's and began employing innovative methods of preventing web scraping such as random timeouts, an unconventional pagination mechanism and applying an MD-5 hash to the User-Agent and requiring it as a mandatory `x-instagram-gis` header on all requests.

The pagination mechanism was a particular focus of ours. Most websites are paginated with use of a GET query parameter, and the next page can be reached by changing `?page=1` to `?page=2`. In this model, scraping is incredibly easy because you just iterate from `1` to `n` and scrape each page. Better still, you create `n` processes and scrape every page concurrently. Instagram's graphql api is paginated with the use of a `cursor` parameter that appears to be a server-generated hash that a scraping client cannot interpret. A given request to Instagram returns a list of results and the `cursor` that will return the next set of results. This effectively prohibits parallelized pagination, as the cursor from page `n` is required to view page `n+1`.

The open source community scrambled to update public libraries to deal with these eccentricities, and we incorporated some of their strategies into this project. This change to the availability of Instagram's data provided motivation for us, as we were curious if our unconventional approach to web scraping would be able to circumvent these measures on its own. If successful, our strategy might be adopted by industry professionals, or even gain the attention of Instagram or Facebook as a loophole in their system.

### A note on "ethical implications"

To be clear, the purpose of this project was not to hack Instagram, nor was it to sell personal information to industry or bad actors. Neither still does this project engage with the heated debate over whether photos posted to "public" profiles should be a matter of public record, which Instagram seemed to believe before the recent scandal. Rather, it sees an interesting application of a distributed architecture to solve problems faced by engineers maintaining more canonical ones. Its progress got bogged down in circumventing the changes to Instagram's api that occured during its development, perhaps due to the sunk-cost fallacy of work already invested in improving collection of the site's data. Better that loopholes (if they exist) be discovered in the course of academic research and the pursuit of intellectual curiosity than exploited by the likes of Cambridge Analytica.

# Solution

Our solution is an application that demonstrates the viability of using serverless technology to create a distributed system for scraping a site like Instagram. To explain how it was designed it is first necessary to describe the various pieces from which it is composed.

### AWS Lambda
Lambda is Amazon's implementation of serverless technology, enabling you to run code without dedicated server instances. We define a set of Lambda functions that emulate the behavior of a server exposing endpoints for initiating scraping jobs, as well as a set of helper functions that are triggered by various events.

### AWS DynamoDB
DynamoDB is Amazon's implementation of a NoSQL database.

### AWS CloudFormation
AWS CloudFormation provides a common language for you to describe and provision all the infrastructure resources in your cloud environment. CloudFormation allows you to use a simple text file to model and provision, in an automated and secure manner, all the resources needed for your applications across all regions and accounts. This file serves as the single source of truth for your cloud environment.

### Serverless Framework
The serverless framework is a provider-indepdendent command-line interface designed to expedite the process of developing and deploying arbitrarily complex cloud-based systems featuring serverless functionality. We have configured it to use AWS as its cloud provider, enabling it to automate the process of deploying our CloudFormation.

### Putting it all together.

We've used the Serverless framework to build and deploy a CloudFormation. Amazon CloudFormation enables you to use a single file to describe a system composed of the various services AWS offers. In our case, the file `serverless.yml` defines three DynamoDB tables for requests, scraping jobs, and the data produced by those scraping jobs (for our purposes, instagram posts). It describes a set of Lambda functions that emulate the behavior of a server that you can make requests to at stable urls. By requesting that the server start a scraping job, it creates a record in DynamoDB describing that job. Creation of that record triggers additional Lambda function invocations that execute the job, breaking up the process of scraping an entire website into individual, isolated calls. When the job is done, the DynamoDb record will be updated to reflect this.


<diagram>


## Design Decisions

- We chose AWS over Google Cloud or Microsoft Azure because its serverless technology appears much more mature to developers that are not extremely familiar with it. At the moment, AWS leads the cloud provider race. While Google Cloud only supports Cloud Functions written in Javascript, Amazon supports Javascript, Python, Java and C#. Part of our metric for this project's success was the speed at which developers could pick up the required technologies and implement it. Very little documentation exists for Google Cloud Functions, particularly their integration with the Serverless framework. This, combined with our team's overwhelming preference for the Python programming language, made AWS the clear choice.

- We chose to use the Serverless framework due to its massive following. With 8k commits, 401 contributors, and 90 releases it is the clear community favorite. The next most popular serverless framework has single digit contributors.

- It's very difficult to verify that a service like Instagram is indeed using rate-limiting on you, or confirm that they have blacklisted your ip address. In order to test our approach we decided to build our own adversarial server to

- Clients don't need to know when jobs are complete. This is because lambda functions have a strict six-second timeout, so if a client attempts to scrape 10,000 instagram posts at once, it will never complete. The unfortunate result of this is that the function must return before the job has finished processing, so clients won't know that a job has completed unless they syncronously query that job until it is marked as omplete. This was acceptable, as no alternative to our system is capable of scraping 10,000 photos at once without eventually get blocked by Instagram, and a system that needs all 10,000 posts before it can continue is poorly designed.

- You can't cancel a job once it's been created. While a more mature implementation of this project would necessarily implement this functionality, this was a convenient assumption for the purpose of scoping our project. It enabled us to assume that the CloudFormation is the only source of updates to the table describing scraping jobs, which guarantees accuracy of the progress of each job. We've configured this table to only be able to perform one query at a time, so that updates will be atomic. We're also using monotonically increasing integers as primary keys in this table, which is terrible design for a truly distributed, large-scale NoSQL database that cannot guarantee uniqueness across shards (the use case DynamoDB was designed for), but under our assumptions of scope it is passable. A more mature implementation might emulate [Instagram's mechanism](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c) for generating unique primary keys across shards.


## Event-Driven Design
We decoupled the logic of initiating a scraping job and executing it. Instead of having a single function that would receive a request, execute the necessary scraping, and return a response, various functions are triggered by events that propogate throughout the CloudFormation.  This decoupling is our optimization for the `cursor` mechanic, as it enables jobs to overlap slightly. For example, a function creates a scraping job in DynamoDB. A second function is triggered by the `INSERT` event, and sends the first request to Instagram. It receives a response and immediately inserts the `cursor`into DynamoDB. While it is processing the list of images, yet another function is triggered by that `INSERT` event that begins the next request. However, it is entirely possible that the time necessary for these events to propogate through the network and trigger the necessary functions is greater than the time saved by this "parallelization," making our implementation ultimately slower than a function that waits on each request before performing the next.

## Ip Rotation
A common technique that many servers and REST APIs utilize involves tracking the ip addresses and user agent details of incoming data requests. If many requests are received from different user agents, then a web scraper may be attempting to scrape data from the website. The servers serving data will then take appropriate steps to reduce such data scraping requests. Similarly, if a server detects excessive requests from the same IP address over a short period of time, the server is likely to blacklist/block requests from that IP. In order to simulate common scraping attacks, we decided to implement a rotating proxy crawler. A rotating proxy crawler would make it much more difficult for any server to necessarily detect suspicious changes in network traffic. Moreover, such a tool would more accurately reveal the potential for data scraping with cloud functions. In order to implement such a tool, first a fake user agent was simulated. A fake user agent is often a string that contains descriptive details about the client. The fake user agent was utilized to retrieve a table of SSL/HTTPS proxies from ssl.proxies.org.

Once proxy IP address and ports were collected, we could rotate proxies every few requests in order to decrease rate request limits. If a proxy ever failed a request, then it was thrown out, and another proxy address was would be randomly selected.

A fake user agent was necessary to obtain proxy addresses to mask other important information. In a request, if only the IP address is different but other pieces of a HTTP request are very similar, the web server is more likely to tag network activity as suspicious.

Utilizing a proxy IP address/port during a request is misleading to the server receiving the request. The server believes that the requests are coming from different locations. We were interested in how a proxy rotation scheme may alter the number of requests for data we could send to a server before getting blacklisted/blocked.


## Adversarial Server


# Results

TRIAL: 10 pages (500 records)

Iteratively scraping 500 records locally, not inserting into database
python trial.py  0.33s user 0.07s system 1% cpu 21.609 total
(50 at a time x 10)

Distributed scraping 500 records, not inserting into database
Scraped 10 pages in 13.193588972091675 +- 1 second
python trial2.py 10  0.49s user 0.09s system 4% cpu 13.514 total

TRIAL 20 pages (1000 records)
Iteratively scraping 1000 records locally, not inserting into database
python trial.py  0.39s user 0.07s system 1% cpu 40.019 total
(50 at a time x 20)

Distributed scraping 1000 records, not inserting into database
Scraped 20 pages in 26.307761907577515 +- 1 second
python trial2.py 20  0.69s user 0.10s system 2% cpu 26.635 total




TRIAL (storing posts)
Iteratively scraping 1000 records locally, inserting into database running locally
(50 at a time x 20)
python trial.py  0.39s user 0.08s system 0% cpu 55.197 total
python trial.py  0.39s user 0.08s system 1% cpu 45.710 total
Total Network Time: 46.362157344818115
Average time per request 2.3181078672409057
python trial.py  0.39s user 0.09s system 1% cpu 46.699 total


Iteratively scraping 1000 records locally, inserting into database running locall
(10 at a time X 100)
Total errors: 1
Total Network Time: 106.97154688835144
Average time per request 1.0805206756399135
python trial.py  0.64s user 0.12s system 0% cpu 1:57.61 total

Finally got one good trial

About 1 / 100 requests fails when scraping instagram due to timeout or just instagram randomly throwing errors
Iteratively Scraping 1000 records remotely, inserting into AWS database
Scraped 100 pages in %s +- 1 second 128.81018805503845

about an hour to scrape 10k pages using the CloudFormation
Scraped 1000 pages in 2995.2664098739624 +- 1 second
python trial2.py 1000 10  43.54s user 3.21s system 1% cpu 49:55.58 total


python trial0.py 10 10  0.52s user 0.07s system 5% cpu 10.686 total

python trial1.py 10 10  0.42s user 0.08s system 4% cpu 10.805 total
python trial1.py 10 10  0.42s user 0.08s system 4% cpu 10.805 total

python trial2.py 10 10  0.52s user 0.09s system 4% cpu 14.909 total

time python trial2.py 1000 10
Scraping 1000 pages of size 10 using AWS lambda + dynamodb triggers
Initializing scrape at https://ebs1rsk4m6.execute-api.us-east-1.amazonaws.com/production/batch_scrape?&location=44961364&start_page=0&end_page=1000&page_size=10

Scraped 1000 pages in 2995.2664098739624 +- 1 second
python trial2.py 1000 10  43.54s user 3.21s system 1% cpu 49:55.58 total


Rough estimates
AWS Lambda Free Tier
1M free requests
400k GB s free = 3.2M seconds


If you assume we use 100mb per s and each call takes 30s, that's 3 GBs
which gives us 100k free requests

at 100 images per request we get 10M free images.

This enables us to do 1000 trials of scraping 10,000 images each.


# Discussion/Next Steps

We gained a lot of hands on experience working with AWS which is an important skill. Dev-ops
A number of steps can be taken to extend the analysis in the project. First, the scraping could be attempted on other popular websites. Instagram gives very limited access to its data to developers and community members. Other systems such as Twitter or LinkedIn might provide different restrictions on accessing data. In an era where access to data is valuable, it is critical to understand the limits of scraping with different technologies. Instagram's REST API system is innovative because it leverages a cursor system that prevents scrapers from parallelizing requests. Other API systems do not necessarily use the concept of cursors. We could build more parallelized lambda function scrapers in such scenarios to get a more accurate picture of how scalable cloud based functions would be. Multithreaded solutions would be an interesting alternative to more thoroughly explore.

Second, we could augment to the features on our adversarial web server. For example, there are advanced features that allow servers to detect requests from potential proxy IP addresses. Adding such features would provide a more comprehensive and realistic view of how effective proxies could be for scraping data from well maintained and relatively secure servers.

Third, as mentioned previously, DynamoDB event triggers were used to speed up the web scraping process. We could utilize different trigger systems instead which may be faster. Specifically, Amazon SNS (Simple Notification Server) and AWS Lambda functions can be integrated so that Amazon SNS system can trigger Lambda functions. When a topic is published to a topic on the SNS system, the Lambda function is invoked with the payload of the published message. This architecture could adopted for scraping purposes. Perhaps the Amazon SNS system provides more efficient event triggering mechanisms than what we used for testing in this paper.

