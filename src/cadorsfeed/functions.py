from lxml import etree
import re
import itertools
import datetime
import uuid
from pyrfc3339 import generate
from geolucidate.functions import get_replacements, google_maps_link
from functools import wraps
from flask import g

from cadorsfeed.aerodromes import replace_aerodromes
from cadorsfeed.filter import make_link, doFilter

extensions = {}
EXTENSION_NS = 'urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd'


def register(func):
    @wraps(func)
    def wrapper(*args):
        return func(*args[1:])
    extensions[(EXTENSION_NS, func.__name__)] = wrapper
    return func


def stripout(things):
    assert len(things) == 1
    return things[0]


@register
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
    out = [doFilter(p, do_geolucidate) for p in out]
    out = [doFilter(p, do_aerodromes) for p in out]
    return out


def do_geolucidate(text):
    return get_replacements(text, google_maps_link(link=make_link))


def do_aerodromes(text):
    return replace_aerodromes(text, make_link)
