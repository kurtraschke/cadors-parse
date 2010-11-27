import json
import re
import urlparse
import urllib
from SPARQLWrapper import SPARQLWrapper, JSON
from decimal import Decimal, setcontext, ExtendedContext
from flask import g, current_app as app
from werkzeug import cached_property

setcontext(ExtendedContext)


class Aerodromes(object):
    @cached_property
    def get_icao_re(self):
        if 'icao_re_cache' not in g.db:
            re_string = r"\b(" + '|'.join([re.escape(c.lstrip("icao:")) for c in g.db.smembers('icao_codes')]) + r")\b"
            g.db.setex('icao_re_cache', re_string, 3600)
        aerodromes_re = re.compile(g.db['icao_re_cache'])
        return aerodromes_re

    @cached_property
    def get_iata_re(self):
        if 'iata_re_cache' not in g.db:
            #Blacklist likely false positives
            blacklist = ["iata:" + c for c in ('ATC', 'SMS', 'DME', 'ANS', 'PAG', 'CNK', 'WJA',
                                               'GPS', 'ACC', 'FSS', 'AKK', 'VIS', 'PAN', 'AMM')]
            re_string = r"\b(" + '|'.join([re.escape(c.lstrip("iata:")) for c in g.db.smembers('iata_codes') if c not in blacklist]) + r")\b"
            g.db.setex('iata_re_cache', re_string, 3600)
        aerodromes_re = re.compile(g.db['iata_re_cache'])
        return aerodromes_re

aerodromes_re = Aerodromes()


def replace_aerodromes(text, link_function):
    substitutions = {}

    def process_matches(matches, lookup):
        for match in matches:
            title = match.group()
            result = lookup(match.group())
            coordinates = result['latitude'] + ',' + result['longitude']
            title = u"{0} ({1})".format(result['name'].decode('utf-8'), coordinates)
            substitutions[match] = link_function(result['airport'], match.group(), title)

    icao_matches = aerodromes_re.get_icao_re.finditer(text)
    process_matches(icao_matches, lambda id: lookup('icao:'+id))
    iata_matches = aerodromes_re.get_iata_re.finditer(text)
    process_matches(iata_matches, lambda id: lookup('iata:' + id))

    return substitutions


def lookup(hashkey):
    keys = ['latitude', 'longitude', 'name', 'airport']
    values = g.db.hmget(g.db[hashkey], keys)
    out = dict(zip(keys, values))
    return out


def fix_coord(value):
    precision = Decimal('0.000001')
    input = Decimal(str(value))
    return str(input.quantize(precision))


def fetch_aerodromes():
    g.db.delete('airports')
    g.db.delete('icao_codes')
    g.db.delete('iata_codes')

    with app.open_resource("dbpedia_query.rq") as queryfile:
        query = queryfile.read()

    limit = 500

    def fetchResults(offset):
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(query % (offset, limit))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        
        for result in results["results"]["bindings"]:
            values = dict([(key, value['value']) for key, value in result.items()])
            values['longitude'] = fix_coord(values['longitude'])
            values['latitude'] = fix_coord(values['latitude'])
            if 'name' not in values:
                values['name'] = urllib.unquote(urlparse.urlparse(values['airport']).path.decode('utf-8').split('/')[-1]).replace('_', ' ')

            airportkey = "airport:"+values['airport']

            g.db.hmset(airportkey, values)
            g.db.sadd('airports', airportkey)

            #Slight hack: we treat FAA LIDs as IATA codes, and TC LIDs as ICAO codes.

            if 'icao' in values:
                key = 'icao:' + values['icao']
                g.db.sadd('icao_codes', key)
                g.db[key] = airportkey
            if 'iata' in values:
                key = 'iata:' + values['iata']
                g.db.sadd('iata_codes', key)
                g.db[key] = airportkey
            if 'lid' in values:
                key = 'icao:' + values['lid']
                g.db.sadd('icao_codes', key)
                g.db[key] = airportkey
            if 'faa' in values:
                key = 'iata:' + values['faa']
                g.db.sadd('iata_codes', key)
                g.db[key] = airportkey

        if len(results["results"]["bindings"]) == limit:
            fetchResults(offset + limit)

    fetchResults(0)
