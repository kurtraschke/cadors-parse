import json
import codecs
import re
import urllib
from os import path
from decimal import Decimal, setcontext, ExtendedContext

from cadorsfeed.utils import db

setcontext(ExtendedContext)

with codecs.open(path.join(path.join(path.dirname(__file__), 'static'),
                           "aerodromes.json"), "r", "utf-8") as aerodromefile:
    aerodromes = json.loads(aerodromefile.read())

aerodrome_re = re.compile('|'.join([r"\b" + re.escape(name) for name in aerodromes.keys()]),
                          re.I)


def get_aerodromes(text, link_function):
    substitutions = {}
    matches = aerodrome_re.finditer(text)

    for match in matches:
        title = match.group()
        result = geocode(match.group())
        if result:
            substitutions[match] = format_link(title, result, link_function)
    return substitutions


def geocode(id):
    key = "cacheaerodrome:" + id
    if not key in db:
        params = {'address': id,
                   'region': 'CA',
                   'sensor': 'false'}
        baseurl = 'http://maps.googleapis.com/maps/api/geocode/json?'
        url = baseurl + urllib.urlencode(params)
        response = urllib.urlopen(url).read()
        db.setex(key, response, 604800)
    else:
        response = db[key]

    response = json.loads(response)

    if (response['status'] == 'OK'):
        result = response['results'][0]
        if ('airport' in result['types']):
            return {'lat': round(result['geometry']['location']['lat']),
                    'lon': round(result['geometry']['location']['lng']),
                    'name': result['formatted_address']}
        else:
            del db[key]
            return None
    else:
        del db[key]
        return None


def round(value):
    precision = Decimal('0.000001')
    input = Decimal(str(value))
    return str(input.quantize(precision))


def format_link(original_string, geocode, link_function):
    baseurl = "http://maps.google.com/maps?"
    coordinates = geocode['lat'] + (',') + geocode['lon']
    params = {'q': u"{0} ({1})".format(coordinates,
                                       geocode['name']).encode('utf-8'),
              'll': coordinates,
              't': 'h'}
    url = baseurl + urllib.urlencode(params.items())
    text = original_string
    title = u"{0} ({1})".format(geocode['name'], coordinates)
    return link_function(url, text, title)
