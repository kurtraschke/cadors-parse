import json
import re
import urllib
from decimal import Decimal, setcontext, ExtendedContext
from flask import g, current_app as app
from werkzeug import cached_property

setcontext(ExtendedContext)

class Aerodromes(object):
    @cached_property
    def get_re(self):
        with app.open_resource("static/aerodromes.json") as aerodromefile:
            aerodromes = json.load(aerodromefile, 'utf-8')
        aerodromes_re = re.compile('|'.join([r"\b" + re.escape(name) + r"\b" for name in aerodromes.keys()]))
        return aerodromes_re

aerodromes_re = Aerodromes()

def get_aerodromes(text, link_function):
    substitutions = {}
    matches = aerodromes_re.get_re.finditer(text)

    for match in matches:
        title = match.group()
        result = geocode(match.group())
        if result:
            substitutions[match] = format_link(title, result, link_function)
    return substitutions


def geocode(id):
    key = "cacheaerodrome:" + id
    if not key in g.db:
        params = {'address': id,
                  'region': 'CA',
                  'sensor': 'false'}
        baseurl = 'http://maps.googleapis.com/maps/api/geocode/json?'
        url = baseurl + urllib.urlencode(params)
        response = urllib.urlopen(url).read()
        g.db.setex(key, response, 604800)
    else:
        response = g.db[key]

    try:
        response = json.loads(response)
    except ValueError:
        del g.db[key]
        return None

    if (response['status'] == 'OK'):
        result = response['results'][0]
        if ('airport' in result['types']):
            for component in result['address_components']:
                if ('establishment' in component['types']) or ('airport' in component['types']):
                    name = component['long_name']
                    break
            else:
                name = result['formatted_address']
            return {'lat': round(result['geometry']['location']['lat']),
                    'lon': round(result['geometry']['location']['lng']),
                    'name': name}
        else:
            #del g.db[key]
            return None
    else:
        del g.db[key]
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
