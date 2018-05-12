# Aerocene

A CloudFormation for distributed, fault-tolerant web scraping.

## Group Members
Jake Seaton, Lisa Vo, Vishal Jain, Divyam Misra

# Abstract

We’ve designed and built a distributed system that uses 'serverless' technology to execute web scraping tasks. The system is deployed as an AWS CloudFormation composed of Lambda, DynamoDB, and APIGateway. It uses the [serverless framework](https://serverless.com/) and [Flask](http://flask.pocoo.org/). By submitting a single request to the Aerocene CloudFormation, the user can create a DynamoDB record of a scraping job to be performed. The system will then automatically distribute all the necessary requests through Lambda functions, and update the record when the job is done. While the system failed to improve the time complexity of scraping as we had hoped, it substantially reduces the overhead necessary to develop and deploy scraping applications, and successfully circumvents complex mechanisms for pagination, rate-limiting, blacklisting and otherwise preventing programatic access to internet content.

# Introduction

Web scraping is a pain. Programs that automate the process of checking for updates to websites enable the creation of incredibly valuable data and powerful software--from legal documents and social media content to recipes and job listings. Unfortunately, without a massive army of dedicated servers, a smaller army of dedicated engineers, and a sophisticated protocol for distributing jobs amongst both, it proves extremely difficult to scrape in a fault-tolerant fashion at scale. Every website is structured differently, and employs different countermeasures to data collection that change without warning. This means that you not only have to write different code for each website you want to scrape, but constantly check those websites to make sure that their structure or various countermeasures haven't changed.

The relatively recent advent of 'serverless' technology, a regrettable misnomer for products such as AWS Lambda and Google Cloud Functions, presents an opportunity to design systems that by nature circumvent some of the biggest challenges to web scraping. The definition of a function can be uploaded to the cloud service provider of choice, and without needing a dedicated server instance the function can be executed at arbitrary scale. These properties align with the ideal web scraper in several ways.

Some things web scraping engineers have to worry about are:

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

The objective of this project was the build an interesting distributed system for performing web scraping tasks using serverless technology. Our hypothesis was that a serverless model would be cheaper, faster to build, and naturally circumvent some of the larger pain points of web scraping development such as rate limiting and blacklisting. We were optimistic that parallelizing across cloud functions might even result in a performance boost.

At the time this project began, Instagram's data was among the most highly coveted by web scrapers. Instagram's API and website made content posted on public profiles readily available to those with a system capable of ingesting the firehose of images and information posted there on a daily basis. Entire companies such as [Trendalytics](https://www.trendalytics.co/), [Influenster](https://www.influenster.com/) and  [Heuritech](https://www.heuritech.com/) have built businesses based on processing the image and textual data of instagram and packaging it for the fashion industry. This  rich, publicly available dataset was therefore the ideal initial target for our scraping strategies.

Shortly after beginning the project, the Cambridge Analytica scandal broke. In response, Instagram and Facebook severely restricted developer access to their api's and began employing innovative methods of preventing web scraping such as random timeouts, an unconventional pagination mechanism and applying an MD-5 hash to the User-Agent and requiring it as a mandatory `x-instagram-gis` header on all requests.

The pagination mechanism was a particular focus of ours. Most websites are paginated with use of a GET query parameter, and the next page can be reached by changing `?page=1` to `?page=2`. In this model, scraping is easy because you just iterate from `1` to `n` and scrape each page. Better still, you create `n` processes and scrape every page concurrently. Instagram's [GraphQL](https://graphql.org/) api is paginated with the use of a `cursor` parameter that appears to be a server-generated hash that a scraping client cannot interpret. A given request to Instagram returns a list of results and the `cursor` that will return the next set of results. This effectively prohibits parallelized pagination, as the cursor from page `n` is required to view page `n+1`.

The open source community scrambled to update public libraries to deal with these eccentricities, and we incorporated some of their strategies into this project. This change to the availability of Instagram's data provided motivation for us, as we were curious if our unconventional approach to web scraping would be able to circumvent these measures on its own. If successful, our strategy might be adopted by industry professionals, or even gain the attention of Instagram or Facebook as a loophole in their system.

### A note on "ethical implications"

To be clear, the purpose of this project was not to hack Instagram, nor was it to sell personal information to industry or bad actors. Neither still does this project engage with the heated debate over whether photos posted to "public" profiles should be a matter of public record, which Instagram seemed to believe before the recent scandal. Rather, it sees an interesting application of a distributed architecture to solve problems faced by engineers maintaining more canonical ones. Its progress got bogged down in circumventing the changes to Instagram's API that occured during its development, perhaps due to the sunk-cost fallacy of work already invested in improving collection of the site's data. Better that loopholes (if they exist) be discovered in the course of academic research and the pursuit of intellectual curiosity than exploited by the likes of Cambridge Analytica.

# Solution

Our solution is an application that demonstrates the viability of using serverless technology to create a distributed system for scraping a site like Instagram. To explain how it was designed it is first necessary to describe the various pieces from which it is composed.

### AWS Lambda
Lambda is Amazon's implementation of serverless technology, enabling you to run code without dedicated server instances. We define a set of Lambda functions that emulate the behavior of a Flask web server exposing endpoints for initiating scraping jobs, as well as a set of helper functions that are triggered automatically by AWS's event system.

### AWS DynamoDB
DynamoDB is Amazon's implementation of a NoSQL database. We use it as a convenient way to persist data between lambda functions, which by nature do not store data. We store records that define scraping jobs as well as the data collected by those jobs. DynamoDB conveniently connects to AWS's event model, enabling us to configure Lambda functions to run whenever a record is created or updated.

### AWS CloudFormation
A CloudFormation is simply a relationship between configurations of other AWS services. The service itself enables you to use a single text file to model and provision, in an automated and secure manner, all the resources needed for an application. This file serves as an idempotent expression of a single source of truth for the distributed system.

### Serverless Framework
The serverless framework is a provider-indepdendent command-line interface designed to expedite the process of developing and deploying arbitrarily complex cloud-based systems featuring serverless functionality. We have configured it to use AWS as its cloud provider, enabling it to automate the process of deploying our CloudFormation.

### Putting it all together.

We've used the Serverless framework to build and deploy a CloudFormation. The file `serverless.yml` defines three DynamoDB tables for requests, scraping jobs, and the data produced by those scraping jobs (in this case, Instagram posts). It describes a set of Lambda functions that emulate the behavior of a server, and points to their definitions in `app.py` and `functions.py`. By requesting that the server start a scraping job, a function creates a record in DynamoDB describing that job. Creation of that record triggers the INSERT event for that table, which another Lambda function listens for and invokes to execute the job, breaking up the process of scraping an entire website into individual, isolated calls. When the job is done, the DynamoDb record will be updated to reflect this.


<img width="1440" alt="screen shot 2018-05-11 at 7 55 46 pm" src="https://user-images.githubusercontent.com/7296193/39952016-674d8e00-5555-11e8-8875-add4388f4be6.png">


## Design Decisions

- We chose AWS over Google Cloud or Microsoft Azure for several reasons. At the moment, AWS leads the cloud provider race. The volume of documentation available for AWS Lambda compared to the analogous services on Cloud and Azure makes it appear much more mature to developers that are not extremely familiar with it. While Google Cloud only supports Cloud Functions written in Javascript, Amazon supports Javascript, Python, Java and C#. Part of our metric for this project's success was the speed at which developers could pick up the required technologies and implement it. This, combined with our team's overwhelming preference for the Python programming language, made AWS the clear choice.

- We chose to use the Serverless framework due to its massive following. With 8k commits, 401 contributors, and 90 releases it is the clear community favorite. The next most popular serverless framework has only single digit contributors. It automated the process of packaging our code as zip files and uploading them to Amazon.

- For testing purposes, we implemented our own adversarial server to simulate the mechanisms we were trying to circumvent. It is very difficult to verify that a service like Instagram has indeed blacklisted or rate-limited you, particularly in a reproducible way. This server (also implemented using Lambda functions emulating a Flask instance) enabled us to test our methods without actually sending too many requests to Instagram.

- We assumed that clients don't need to synchronously know when jobs are complete. This is because lambda functions have a strict six-second timeout, so if a client attempts to scrape 10,000 instagram posts at once, the lambda function waiting for it will timeout before it completes. The unfortunate result of this is that the function must return before the job has finished processing, so clients won't know that a job has completed unless they send an additional query to check on its progress. Our trial script uses a while loop to check if the scraper is done once per second. This was acceptable, as no alternative to our system is capable of scraping 10,000 photos at once without eventually get blocked by Instagram, and a system that needs all 10,000 posts before it can continue is itself poorly designed.

- Finally, for the moment you can't cancel a job once it's been initiated. While a more mature implementation of this project would enable this functionality, this was a convenient assumption for the purpose of scoping our project. It enabled us to further assume that the CloudFormation is the only source of updates to the table describing scraping jobs, which guarantees accuracy of the progress of each job. We've configured this table to only be able to perform one query at a time so that updates will be atomic. We're also using monotonically increasing integers as primary keys in this table, which is terrible design for a truly distributed, large-scale NoSQL database that cannot guarantee uniqueness across shards (the use case DynamoDB was designed for), but under our assumptions of scope it is passable. A more mature implementation might emulate [Instagram's mechanism](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c) for generating unique primary keys across shards.


## Event-Driven Design
We decoupled the logic of initiating a scraping job and executing it. Instead of having a single function that would receive a request, execute the necessary scraping, and return a response, various functions are triggered by events that propogate throughout the CloudFormation.  This decoupling is our optimization for the `cursor` mechanic, as it enables jobs to overlap slightly. For example, a function creates a scraping job in DynamoDB. A second function is triggered by the `INSERT` event, and sends the first request to Instagram. It receives a response and immediately inserts the `cursor` into DynamoDB. While it is processing the list of images, yet another function is triggered by that `INSERT` event to begin the next request. However, it is entirely possible that the time required for these events to propogate through the network and invoke the necessary functions is greater than the time saved by this "parallelization," making our implementation ultimately slower than a single-threaded function that waits on each request before performing the next.

## IP Rotation
A common technique that many websites and REST APIs use involves tracking the ip addresses and user agent details of incoming requests. If too many requests are received from the same address or agent, it's likely that your site is being scraped. To try to trick our own adversarial server, and potentially a website like Instagram, we implemented a system for rotating requests between anonymous proxies, to avoid detection, rate limiting, and blacklisting.

To do this we use a python library for generating fake user agents combined with the table of public SSL/HTTPS proxies on [ssl.proxies.org](ssl.proxies.org). Then, each outgoing request can simply select a random proxy and user agent to masquerade as when making a query to our server. If a proxy ever failed a request, then it was thrown out, and another proxy address was would be randomly selected. The user agent randomization was important, because some servers get suspicious when the ip address of a request is different but everything else is the same.

Because interacting with Instagram's servers can result in ambiguous and unexpected errors (aside from a typical HTTP 429 `Too Many Requests` error, we also encountered 500 and 403 errors randomly during testing) and because we don't know exactly how Instagram implements its rate-limiting techniques, in order to create a controlled testing environment we decided to build our own adversarial server that mimics the behavior of a typical web server with anti-scraping mechanisms. Our adversarial server supports three canonical defense protocols against bad actors (in this case, malicious scrapers): rate-limiting, blacklisting, and exponential backoff. 

In rate-limiting, a user is only allowed to send a server a certain number of requests within each window of time (the length of which is defined by the server). After exceeding the maximum number of requests, the user`s IP address is temporarily blocked until the next window of time. Blacklisting works the same way; however, once the user has exceeded the max number of requests she is forever blocked and this state persists through all subsequent time frames. Finally, in exponential backoff, the user is made to wait an exponentially increasing amount of time between requests. That is, on the nth request, she must wait 2^n seconds before her request is processed.  

In our design, each time a request is received the IP address is logged in a DynamoDB database along with two properties: request_count and blacklisted. `Request_count` is a counter that increments with each request received in a time frame and resets with each new window of time. `Blacklisted` is a boolean that indicates whether an IP address has been blacklisted or not. Each of the three protocols has a set number of MAX_REQUESTS that a user can send before she is blocked from sending any more within that time frame (unless she is blacklisted, in which case she would also be blocked from sending requests in subsequent time frames). We introduced a `clearing` function to reset all request_count counters at the end of a time frame while keeping record of blacklisted users. 

We pitted our adversarial server against two bad actors: a client using IP proxy rotation and a simpler client using a single IP address. For the proxy rotation, we drew upon a list of 100 valid proxies and a proxy was selected at random for each request (in order to avoid using proxies in a detectable pattern that an advanced adversary like Instagram might discover). As expected, for the rate-limiting protocol, the client using a single IP address was blocked after exceeding MAX_REQUESTS (10) in a single time frame (1 minute). However, the client using IP proxy rotation remained unblocked through the time frame. With 100 proxies to draw from, it makes sense that no one proxy would send enough requests to be blocked. Even if one proxy did get blocked, the next request would likely be masked with a different proxy. 

For the blacklisting protocol, we allowed three time frames to pass with MAX_REQUEST=5. The simpler client was unsurprisingly blacklisted within the first time frame and remained blacklisted through the next two time frames. The other client was able to outsmart the server throughout all three time frames, even with four proxies getting blacklisted. Although requests by blacklisted proxies were denied, the client could quickly send a new request under a different proxy. 

For the exponential backoff protocol, the simpler client experienced increasing wait times between requests as expected. After a certain point (which occurred very quickly), the client`s connection timed out and the client was no longer able to ping successful requests to the server. However, for the client using proxy rotation, wait times were mostly nonexistent during the first 30 seconds as new proxies were rotated. Afterward, wait times increased a small amount as proxies were revisited. If we had let the client keep running, eventually timeout errors would also occur as all proxies get used the maximal number of times; however, this would happen much later compared to the simple client.

While we were successfully able to trick our own server using this method, we ultimately didn't need to use it as part of the CloudFormation for scraping Instagram, because using AWS Lambda sufficiently distributed requests between enough locations in the cloud to avoid detection.

# Results
We ran a series of trial scripts to test the performance of the three configurations:

<img width="1440" alt="screen shot 2018-05-11 at 8 20 56 pm" src="https://user-images.githubusercontent.com/7296193/39952280-d8e755e8-5558-11e8-8321-d4d59b39190a.png">

- Trial 0 scrapes instagram directly from the local machine.

- Trial 1 scrapes Instagram through AWS Lambda.

- Trial 2 scrapes Instagram using a live Aerocene CloudFormation.


| Scraping 500 Records | 10 x 50  | 20 x 25 | 25 x 20  |
|----------------------|----------|---------|----------|
| Trial 0              | 17.86    | 31.74   | 36.16    |
| Trial 1              | 26.14    | 36.5    | 49.76    |
| Trial 2              | 87.96    | 91.5    | 92.3     |

Each cell in the table represents the average time of five runs of a particular trial. We ran each trial using three different ways to reach the desired number of records. For example, `10 x 50` means sending ten requests that each scrape fifty records from Instagram.

| Scraping 1000 Records | 20 x 50  | 40 x 25 | 25 x 40  |
|-----------------------|----------|---------|----------|
| Trial 0               | 33.16    | 51.8    | 60.14    |
| Trial 1               | 56.95    | 84.81   | 97.52    |
| Trial 2               | 190.1    | 195.2   | 215      |

While Trials 1 and 2 never got blocked by Instagram, Trial 0 was frequently blocked when it tried to send double digit requests in a short amount of time.


<img width="1440" alt="screen shot 2018-05-11 at 9 00 51 pm" src="https://user-images.githubusercontent.com/7296193/39952543-96d0d642-555e-11e8-960c-a28622a6eb25.png">

This chart compares the performance of the three systems when used to scrape 500 vs. 1000 records. As we might expect, it took approximately twice as long to scrape 1000 records than it took to scrape 500 records in all cases. This is a good result, as it confirms that the complexity of scraping using any of the systems is linear in the number of records being scraped.

<img width="1440" alt="screen shot 2018-05-11 at 9 01 05 pm" src="https://user-images.githubusercontent.com/7296193/39952542-96c20e28-555e-11e8-8656-2cf34ce9c6df.png">

This chart compares the performance of the three systems across the different ways to scrape 500 records. It appears that in all cases scraping fewer, larger pages is better than many smaller pages. This helps us to understand why Instagram, in an attempt to restrict access to its data, would reduce the maximum page size with which third parties could access its data.

# Discussion

Both charts indicate that Aerocene is generally slower than scraping iteratively, but not exponentially so, which means that it may be worth using to scrape systems such as Instagram that frequently block implementations such as the local trial.

It makes sense that running a single-threaded scraper locally was faster than sending instructions to and from AWS and waiting for events to propagate and trigger lambda functions. In the first case you are sending requests to Instagram, while in the second case you are sending requests to a system that then performs other work before eventually sending the same requests to Instagram.

Therefore, these results invalidated our hypothesis that Aerocene could effectively "parallelize" on Instagram's unique cursor architecture to outperform canonical scraping, but confirmed that it would perform better against systems inclined to block repeat visitors. The local scraper was blocked frequently, and couldn't reliably send more than 100-200 requests in a row without Instagram picking up on it.

The second fastest configuration was using lambda functions in the cloud to perform the actual scraping. This is exactly the same as running it locally, except you’re also paying Amazon to function as a proxy for the requests you would otherwise be making directly. This was effective at preventing the local machine from getting blacklisted, but wastes a lot of resources on round trips to and from AWS, and the local machine must wait longer on each request to begin the next scrape.

While the slowest, Aerocene was the only configuration that freed the local machine to do other things while the job was being performed. It was also the only configuration to also store the scraped information in a database.

# Next Steps

A number of steps can be taken to extend the analysis in the project. First, the scraping could be attempted on other popular websites. Instagram gives very limited access to its data to developers and community members. Other systems such as Twitter or LinkedIn might provide different restrictions on accessing data. In an era where access to data is valuable, it is critical to understand the limits of scraping with different technologies. Instagram's REST API system is innovative because it leverages a cursor system that prevents scrapers from parallelizing requests. Other API systems do not necessarily use the concept of cursors. We could build more parallelized lambda function scrapers in such scenarios to get a more accurate picture of how scalable cloud based functions would be. Multithreaded solutions would be an interesting alternative to more thoroughly explore.

Second, we could augment to the features on our adversarial web server. For example, there are advanced features that allow servers to detect requests from potential proxy IP addresses. Adding such features would provide a more comprehensive and realistic view of how effective proxies could be for scraping data from well maintained and relatively secure servers.

Third, as mentioned previously, DynamoDB event triggers were used to speed up the web scraping process. We could utilize different trigger systems instead which may be faster. Specifically, Amazon SNS (Simple Notification Server) and AWS Lambda functions can be integrated so that Amazon SNS system can trigger Lambda functions. When a topic is published to a topic on the SNS system, the Lambda function is invoked with the payload of the published message. This architecture could adopted for scraping purposes. Perhaps the Amazon SNS system provides more efficient event triggering mechanisms than what we used for testing in this paper.

We gained a lot of hands on experience working with AWS which is an important skill. Dev-ops is hard...



