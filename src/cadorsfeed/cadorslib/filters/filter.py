import lxml
import lxml.sax
from xml.sax.handler import ContentHandler

NS = 'http://www.w3.org/1999/xhtml'

NSMAP = {'h': 'http://www.w3.org/1999/xhtml',
         #'a': 'http://www.w3.org/2005/Atom',
         'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'}


def make_link(url, text, title, css_class='geolink', coordinates=None):
    def output_link(out):
        parameters = {('', 'href'): url,
                      ('', 'title'): title}
        if css_class is not None:
            parameters[('', 'class')] = css_class
        if coordinates is not None:
            parameters[('http://www.w3.org/2003/01/geo/wgs84_pos#',
                        'lat')] = coordinates['latitude']
            parameters[('http://www.w3.org/2003/01/geo/wgs84_pos#',
                        'long')] = coordinates['longitude']
        out.startElementNS((NS, 'a'), 'a', parameters)
        out.characters(text)
        out.endElementNS((NS, 'a'), 'a')
    return output_link


def make_span(text, title, css_class='geolink', coordinates=None):
    def output_span(out):
        parameters = {('', 'title'): title}
        if css_class is not None:
            parameters[('', 'class')] = css_class
        if coordinates is not None:
            parameters[('http://www.w3.org/2003/01/geo/wgs84_pos#',
                        'lat')] = coordinates['latitude']
            parameters[('http://www.w3.org/2003/01/geo/wgs84_pos#',
                        'long')] = coordinates['longitude']
        out.startElementNS((NS, 'span'), 'span', parameters)
        out.characters(text)
        out.endElementNS((NS, 'span'), 'span')
    return output_span


#There _is_ a cleaner way to replace text with an Element,
#but only marginally cleaner.
class FilterContentHandler(ContentHandler, object):

    def __init__(self, replacement_function):
        self.out = lxml.sax.ElementTreeContentHandler()
        self.replacement_function = replacement_function
        self.openElements = []

    def characters(self, data):
        if 'a' in self.openElements:
            #Don't perform replacement inside an existing link.
            self.out.characters(data)
            return

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
        for prefix, namespace in NSMAP.iteritems():
            self.out.startPrefixMapping(prefix, namespace)

    def endDocument(self, *args):
        assert len(self.openElements) == 0
        for prefix, namespace in NSMAP.iteritems():
            self.out.endPrefixMapping(prefix)
        self.out.endDocument(*args)

    def startElementNS(self, *args):
        self.openElements.append(args[0][1])
        self.out.startElementNS(*args)

    def endElementNS(self, *args):
        assert self.openElements.pop() == args[0][1]
        self.out.endElementNS(*args)

    def getOutput(self):
        return self.out.etree.getroot()


def do_filter(input_doc, replacement_function):
    handler = FilterContentHandler(replacement_function)
    lxml.sax.saxify(input_doc, handler)
    return handler.getOutput()
