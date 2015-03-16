"""
    Parallization Mixins

    Framework to scale out any class method workload. 

    This allows for job queueing, result retrival

    Worker_base:
      interface for any worker mixin
    Worker_inmemory:
      Using inmemory only data structures : Queue/Hashmap 
       parallalize N threaded workers that fetch jobs from the Queue, and place results
       into the hash.

      This will only scale to the limitations of the machine, and the python GIL

    Todo:
    Worker_AWS:
      Use SQS to provide the queueing layer, and DynamoDB for job results. This would allow for very
      easy horizontal scaling. In fact the entire unit of work could be placed into AWS Lambda
      removing the need to have a dedicated server at all. 

    worker_loop timeouts      
"""

import queue
import logging
import threading
import time
import random
import pprint
import uuid
import copy
import collections

log = logging.getLogger(__name__)

class Worker_base():
  """ Specify interface for Worker mixins """
  pass
  
  def add_work(self, payload):
    assert False

  def do_work(self, param):
    assert False

  def get_result(self):
    assert False
  
  def add_workers(self, count):
    for x in range(count):
      zthread = threading.Thread(target=self._worker_loop)
      zthread.daemon=True
      zthread.start()
  
  def _worker_loop(self):
    pass

class Worker_inmemory(Worker_base):
  """ 
    Queue/Parallel worker mixin keeping state in memory
  """

  def __init__(self, *a, **kw):
    self._work_queue = queue.Queue()
    self._work_lock = threading.RLock()
    self._work_result = {}
    super().__init__(*a, **kw)

  def add_work(self, payload):
    """ Accept a new unit of work to the Job Queue, create a token to track this job, 
        and reserve this token against other jobs
    """

    #Tokens randomly generated, in a real environment user credentails and encryption are a must
    #   Tokens would only be mapable to the account they are permissioned for. 

    #Ensure token is unique
    token = str(uuid.uuid4().hex)
    with self._work_lock:
      while(token in self._work_result):
        token = str(uuid.uuid4().hex)
     
      #Create job metadata 
      self._work_result[token] = collections.defaultdict(dict)
      self._work_result[token]['enqueued_s'] = time.time()
      self._work_result[token]['payload'] = payload
      self._work_queue.put_nowait((payload,token))
    
    log.info("%s worker enqueue %i", 
              self.__class__.__name__, 
              self._work_queue.qsize())
    return token

  def get_result(self, token, debug=False):
    """
      Given a token lookup job status, if jobid doesn't exist KeyError will be raised
    """
    log.info(pprint.pformat(self._work_result))
    with self._work_lock:
      if debug:
        return copy.deepcopy(self._work_result[token])
      return copy.deepcopy(self._work_result[token]['result'])

  def _put_result(self, token, result):
    """
      Insert result into job metadata
    """
    with self._work_lock:
      self._work_result[token]['finished_s'] = time.time() 
      self._work_result[token]['result'] = result

  def _get_work(self):
    """
      Simply dequeue the next available job, blocking if none is available
    """
    value = self._work_queue.get()
    log.debug("%s worker dequeue %i - %s", 
              self.__class__.__name__,
              self._work_queue.qsize(), 
              value)
    return value
  
  def _worker_loop(self):
    """
      Given threaded workers, absorb any exceptions so threads don't die.
      File away job results when availble.
    """
    while(True):
      try:
        log.info("%s worker ready" % self.__class__.__name__)
        payload, token = self._get_work()
        log.info("worker processing %s %s", token, payload)
        try:
          result = self.do_work(payload)
          log.info("worker saving result %s %s", token, result)
          self._put_result(token, result) 
        except Exception as e:
          self._put_result(token, str(e)) 
          raise
      except Exception as e:
        log.error(e)



if(__name__ == "__main__"):
  """
    Extremely basic testing
  """
  
  class test_work(Worker_inmemory):
    total_out = 0
    total_in = 0
    lock = threading.RLock()
    def do_work(self, payload):
      timeout, string = payload 

      log.info("%s - sleep %i", string, timeout) 
      time.sleep(timeout)
      with self.lock:
        self.total_in += 1
      log.info("%s finish in %i out %i"% ( string, self.total_out, self.total_in))
 
  logging.basicConfig(level=logging.DEBUG)
  log.info("Starting up test bench")

  tw = test_work()
  tw.add_workers(5)
  for x in range(10):
    r = random.randint(0,5)
    with tw.lock:
      tw.total_out +=1
    tw.add_work((r, str(r)))

  while(tw.total_out != tw.total_in):
    time.sleep(1)
 
  log.info("Success") 
