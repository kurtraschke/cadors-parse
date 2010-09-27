import lxml
import lxml.sax
from lxml import etree
from xml.sax.handler import ContentHandler

NS = "http://www.w3.org/1999/xhtml"


def make_link(url, text, title):
    def output_link(out):
        out.startElementNS((NS, 'a'), 'a', {('', 'href'): url,
                                            ('', 'title'): title,
                                            ('', 'class'): 'geolink'})
        out.characters(text)
        out.endElementNS((NS, 'a'), 'a')
    return output_link


#There _is_ a cleaner way to replace text with an Element, but only marginally cleaner.
class FilterContentHandler(ContentHandler, object):

    def __init__(self, replacement_function):
        self.out = lxml.sax.ElementTreeContentHandler()
        self.replacement_function = replacement_function

    def characters(self, data):
        after = data
        offset = 0
        replacements = self.replacement_function(after).items()
        replacements.sort(key=lambda x: x[0].start())
        for (match, link) in replacements:
            content = match.group()

            start = match.start() - offset
            end = match.end() - offset

            before = after[:start]
            after = after[end:]

            self.out.characters(before)
            link(self.out)

            offset += end
        self.out.characters(after)

    def startDocument(self, *args):
        self.out.startDocument(*args)
        self.out.startPrefixMapping('h', NS)

    def endDocument(self, *args):
        self.out.endPrefixMapping('h')        
        self.out.endDocument(*args)

    def startElementNS(self, *args):
        self.out.startElementNS(*args)

    def endElementNS(self, *args):
        self.out.endElementNS(*args)

    def getOutput(self):
        return self.out.etree.getroot()


def doFilter(input, replacement_function):
    handler = FilterContentHandler(replacement_function)
    lxml.sax.saxify(input, handler)
    return handler.getOutput()
