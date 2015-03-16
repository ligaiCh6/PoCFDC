"""
There is alot of indeterminism in what constitutes a word on a website:
  Just USEnglish alpabetical characters? Numbers?
  Non-rendered comments? Javascript injected text?
  Title Text?

  Since HTML has many different rendering possibilities, its a difficult problem
  to say what is visible on the standard set of browsers IE,Chrome,Firefox

  We can tokenize all returned text and count that as words,
    Even though <div> : would count as a word

  We can only parse the data segment of a page, but this is still a very rough
    metric. 

  We can specify which html tags we consider visible, and tokenize those words. 

  --- It's a non-trivial, ambigious, problem. Simply running strings on a html
      document seems insufficient. ---

  Rending via Selenium would be the next logical step for this class

  For the moment - we will take a tournament count via several different methods:
    The lowest visible word count wins

  ----
    Known issues:
      min probably isn't robust for all display types
      assuming utf-8 encoding
      memory footprint, protect against unbounded inputs
"""

import pprint
import urllib.request
import re
import logging
# HTML Parsers
import html.parser
import bs4 #3rd party MIT licensed html parser
import html2text #3rd party GPL html parser

log = logging.getLogger(__name__)

class PageRetrivalCount(object):
  """ Namespace Aggegrator """

  #Network operation timeout
  timeout_s = 5

  #What counts as a word?
  word_re = re.compile("[a-zA-Z]+")

  protocol_re = re.compile("^[a-zA-Z]+\://")
  class HTMLwc(html.parser.HTMLParser):
    """ Subclass engine to do word parsing in the data segment as defined
        by HTMLParser """
    def __init__(self, *a, **kw):
      self.word_count=0
      super().__init__(*a, **kw)

    def handle_data(self, data):
      self.word_count += len(PageRetrivalCount.word_re.findall(data))

    def get_wc(self):
      return self.word_count

  @classmethod
  def ParseCount_stdlib(cls, html): 
      parsed_count = cls.HTMLwc()
      parsed_count.feed(html)
      return parsed_count.get_wc()

  @classmethod
  def ParseCount_beautifulsoup(cls, html):
      """
        Parse and attempt to exact only visible regions using the beautiful 
        soup parser
      """
      soup = bs4.BeautifulSoup(html)

      for e in soup.findAll(text=True):
        # Filter by element types for a, p, title

       #This magical list of non-visible elements courtesty of:
       # https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text/1983219#1983219
       if(e.parent.name in ('script', 'style', 'head', 'title') or
          isinstance(e, bs4.Comment)):
          e.extract()

      return len(cls.word_re.findall(soup.get_text()))

  @classmethod  
  def ParseCount_html2text(cls,html):
      """ 
        Parse and extract visible region using html2text library
      """
      return len(cls.word_re.findall(html2text.html2text(html)))

  @classmethod
  def CountURL(cls,url):
    """
      For every url, download the body, if possible
      Perform word counts using all of our html parsers, return a tuple
      with the minimum word count, followed by each parsers individual count 
    """

    #If no protocol is specified default to http
    if(not cls.protocol_re.match(url)):
      url = "".join(("http://", url))
    with urllib.request.urlopen(
        url,
        timeout=cls.timeout_s) as result:
        raw_response = result.read().decode('utf-8')

    VisibleParsers = (
      cls.ParseCount_stdlib,
      cls.ParseCount_beautifulsoup,
      cls.ParseCount_html2text
    )

    results = list(map(lambda x: (x.__name__,x(raw_response)), VisibleParsers))
    log.info("%s -- %s", url, results)
    lowest_count = min(map(lambda x: x[1], results)) 

    return {'count' : lowest_count, 'debug_counts_by_parser' : results}


if (__name__=="__main__"):
  """
    Extremely basic testing framework
  """

  Test_URLs = """
                http://bash.org/?85514
                http://example.com
                http://catless.ncl.ac.uk/Risks/28.55.html
                http://www.pvv.ntnu.no/~steinl/vitser/bofh.txt
              """.split()

  for u in Test_URLs:
    print("\t%s - %s" % (u, 
                PageRetrivalCount.CountURL(u)))


