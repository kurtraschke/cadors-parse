from lxml import etree
import re
import itertools
import datetime
import uuid
from pyrfc3339 import generate
#from geolucidate.functions import get_replacements
#from geolucidate.links.google import google_maps_link
from functools import wraps
from flask import g

from cadorsfeed.filters.aerodromes import replace_aerodromes
from cadorsfeed.filters.link_cadors import replace_cadors_links
#from cadorsfeed.filters.filter import make_link, doFilter

extensions = {}
EXTENSION_NS = 'urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd'


def register(func):
    @wraps(func)
    def wrapper(*args):
        return func(*args[1:])
    extensions[(EXTENSION_NS, func.__name__)] = wrapper
    return func


def stripout(things):
    assert len(things) == 1, things
    return things[0]


@register
def strip_nbsp(to_strip):
    if isinstance(to_strip, list):
        if len(to_strip) == 0:
            return None
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
    return string
#return element

"""
@register
def fix_names(names):
    return [elementify(s) for s in set([fix_name(name) for name in names])]


@register
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


@register
def produce_id(cadors_number):
    cadors_number = stripout(cadors_number)
    key = "cacheuuid:" + cadors_number

    if not key in g.db:
        g.db[key] = uuid.uuid4().urn

    return g.db[key]


@register
def content(content_list):
    paras = itertools.chain.from_iterable([block.split('\n')
                                           for block in content_list])
    out = [elementify(strip_nbsp(p)) for p in paras]
    filters = [lambda text: get_replacements(text, google_maps_link(link=make_link)),
               lambda text: replace_aerodromes(text, make_link),
               lambda text: replace_cadors_links(text, make_link)]
    for filter in filters:
        out = [doFilter(p, filter) for p in out]
    return out
"""
