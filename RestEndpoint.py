"""
    Flask RESTful webserver

      Two endpoints
        /fdctest/url/<string>
          returns a json object with id defined
 
        /fdctest/count/<string>
          Given a ID supplied above returns a json object with count defined 
            where count is the number of words available on the website
            supplied from the /url/ endpoint

    Todo - 
      Unit tests
      argparse command line options instead of bundling into the program
"""

import logging
import flask
import flask.ext.restful
import flask.ext.restful.reqparse
import urllib
import pprint
import PageRetrivalCount
import Worker
import argparse

class CountAtScale(
            PageRetrivalCount.PageRetrivalCount, 
            Worker.Worker_inmemory):
    """
      Amalgam of our website parsing and counting, plus our parallization class
    """

    def do_work(self, url):
      return self.CountURL(url)

    def get_result(self, token,*a,**kw):
      """
        Inserting some debug instrumentation
      """
      result = super().get_result(token,*a,**kw)

      log.info("%s returning result for %s - %s", self.__class__.__name__,
                                                token, result)
      return result

CAS = CountAtScale() 
#DoP of 10
CAS.add_workers(10)

class fdctest_url(flask.ext.restful.Resource):
  """
    Query acceptance endpoint
  """

  CAS = CAS
  def __init__(self, *a, **kw):
    super().__init__(*a, **kw)
 
  def process(self,url):
    return {'id': CAS.add_work(url), 'Message': 'Enqueued'}, 202
  get = process
  put = process


class fdctest_count(flask.ext.restful.Resource):
  """
    Check job status, and return result if available
  """
  CAS = CAS
  def __init__(self, *a, **kw):
    self.parser = flask.ext.restful.reqparse.RequestParser()	
    #self.parser.add_argument('token', dest='token',
    #                        type=str, required=True,
    #                        )
    self.parser.add_argument('debug', dest='debug',
                            type=bool, required=False,
                            default=False
                            )
    super().__init__(*a, **kw)

  def process(self, token):
    """
      If the job doesn't exist return a 404
      If the job exists, but doesn't have any results, return full debug stack on job
    """
    args = self.parser.parse_args()
    try:  
      return CAS.get_result(token, debug=args.debug), 200
    except KeyError as exp:
      try:
        return CAS.get_result(token, debug=True), 100
      except KeyError as exp:
        return "Token not found", 404 
      raise
        
  get = process


class ThisFlask(flask.Flask):
    """
      Prepend our base url to all endpoints
    """

    def add_url_rule(self, base, *a, **kw):
      super().add_url_rule("/fdctest%s"%base,*a,**kw)

# Setup loggin, start flask
if(__name__ == "__main__"):

  logging.basicConfig(level=logging.DEBUG)
  log = logging.getLogger(__name__)
  app = ThisFlask(__name__)
  api = flask.ext.restful.Api(app)

  api.add_resource(fdctest_url, '/url/<path:url>')
  api.add_resource(fdctest_count, '/count/<token>')

  log.info("Starting Flask Server")
  for r in app.url_map.iter_rules():
      log.info("Flask - Endpoint - %s %s %s",r.endpoint, " ".join(r.methods), r)

# Run our server
app.run(
      threaded = True, 
      host = '0.0.0.0',
      port = 23231
      )

