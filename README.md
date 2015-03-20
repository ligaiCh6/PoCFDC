Problem Statement:

Need a RESTful API where user gives a web url and expects to get the number of words in that webpage.
 
Code to develop:

Will have the above stated problem solved using 2 RESTful endpoints.

Restful endpoint – 1: 
Input: web url 
Output: A unique id
Description: Reads web url from the request and returns a "unique id" which can be referenced by the client
sample request url : http://localhost:8080/fdctest/url/www.example.com
sample reply in json: { “id”:”123456”}
 
Restful endpoint – 2:
Input:  "unique id" 
Output: word count
Description: Reads the "unique id" from the request and returns the number of words of that "unique id".
sample request url: http://localhost:8080/fdctest/count/123456
sample reply in json: { “count”: “100”}

All code has to be written in python.


-------------------------------
Writup of solution 


The code is running on a public server for the next 48 hours. The endpoints are here:

$ curl 54.177.191.172:23231/fdctest/url/http://catless.ncl.ac.uk/Risks/28.55.html
{"Message": "Enqueued", "id": "681dc29238f743b3b4a9c14366421cc0"}

$ curl 54.177.191.172:23231/fdctest/count/681dc29238f743b3b4a9c14366421cc0
{"count": 7133, "debug_counts_by_parser": [["ParseCount_stdlib", 7166], ["ParseCount_beautifulsoup", 7133], ["ParseCount_html2text", 7671]]}

Launching the server: 

$ python3 ./RestEndpoint.py
INFO:__main__:Starting Flask Server
INFO:__main__:Flask - Endpoint - static GET HEAD OPTIONS /fdctest/static/<path:filename>
INFO:__main__:Flask - Endpoint - fdctest_count GET HEAD OPTIONS /fdctest/count/<token>
INFO:__main__:Flask - Endpoint - fdctest_url PUT GET HEAD OPTIONS /fdctest/url/<path:url>
INFO:werkzeug: * Running on http://0.0.0.0:23231/ 

Timeframe 20150315:1600PST-0200PST. 
 
Thoughts:
   There is ambiguity over what constitutes a word. Simple alphabetical, alphanumeric, or unicode token blocks? Which part of a website is relevant for this purpose?

   I've made the operational assumption that we only care about English alphabet strings of 1 or more characters, that are rendered on visible portions of a website. That is to say: html comments/javascript/doc elements, etc, do not count. Since word visibility on a html page is a highly interpretive problem;  I wired up 3 html parsers. I take the minimum word count across all visible text parsers, to err on the side of too-few rather then too-many. 

   The Parallelism is provided by Python threading and a in-memory job queue. Though I did design the parallelism class to accept future mixins for easy expansion into AWS. 

   The RESTful backend is powered by flask. 

Issues;
   Originally I had intended to provide a implementation that could either run in memory or backed by AWS, but I went down the rabbit hole of html visible element parsing. 
   Testing is very raw - and manual, a proper framework is needed to provide any level of confidence for future development. 
   Input validation is not seriously performed, and there is no concept of security or idempotency built into the interface. 
   argparse should have been used for all parameters, to be supplied on the command line with defaults sourcing from a configuration file. 
