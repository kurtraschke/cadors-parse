from lxml import etree
import re
import itertools
import datetime
from pyrfc3339 import generate
from geolucidate.functions import get_replacements, google_maps_link
from cadorsfeed.cacheuuid import cacheuuid

extensions = {}


def register():
    def decorate(func):
        def wrapper(*args):
            return func(*args[1:])
        extensions[('urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd',
                    func.__name__)] = wrapper
        return func
    return decorate

def stripout(things):
    assert len(things) == 1
    return things[0]

@register()
def strip_nbsp(to_strip):
    if isinstance(to_strip, list):
        to_strip = stripout(to_strip)
    return to_strip.rstrip(u'\xa0')

def fix_name(name):
    name = strip_nbsp(name)
    (last, first) = name.split(", ")
    return first + " " + last

def elementify(string):
    element = etree.Element("{http://www.w3.org/1999/xhtml}p",
                            nsmap={'h': 'http://www.w3.org/1999/xhtml'})
    element.text = string
    return element

@register()
def fix_names(names):
    return [elementify(s) for s in set([fix_name(name) for name in names])]


@register()
def fix_datetime(date, time):
    datere = re.compile(r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})")
    dateparts = datere.search(strip_nbsp(date)).groupdict()

    timere = re.compile(r"(?P<hour>[0-9]{2})(?P<minute>[0-9]{2}) Z")
    result = timere.search(strip_nbsp(time))
    if result:
        timeparts = result.groupdict()
    else:
        timeparts = {'hour': 0, 'minute': 0}

    ts = datetime.datetime(int(dateparts['year']),
                           int(dateparts['month']),
                           int(dateparts['day']),
                           int(timeparts['hour']),
                           int(timeparts['minute']))

    return generate(ts, accept_naive=True)

@register()
def produce_id(cadors_number):
    cadors_number = stripout(cadors_number)

    return cacheuuid(cadors_number)

@register()
def content(content_list):
    paras = itertools.chain.from_iterable([block.split('\n')
                                           for block in content_list])
    out = [elementify(strip_nbsp(p)) for p in paras]
    do_geolink(out)
    return out

#Surely there must be a cleaner way to replace text with an Element in lxml.
def do_geolink(paras):
    for p in paras:
        replacements = get_replacements(p.text,
                                        google_maps_link(link=make_link)).items()
        replacements.sort(key=lambda x: x[0].start())

        element = p
        offset = 0
        for (match, link) in replacements:
            start = match.start() - offset
            end = match.end() - offset

            if element is p:
                string = element.text
                element.text = string[:start]
                element.append(link)
            else:
                string = element.tail
                element.tail = string[:start]
                element.getparent().append(link)
            link.tail = string[end:]
            assert string[start:end] == match.group(), (string[start:end],
                                                        match.group())
            element = link
            offset += end

def make_link(url, text, title):
    element = etree.Element("{http://www.w3.org/1999/xhtml}a",
                            nsmap={'h': 'http://www.w3.org/1999/xhtml'})
    element.text = text
    element.attrib['href'] = url
    if title != '':
        element.attrib['title'] = title
    element.attrib['class'] = "geolink"
    return element
