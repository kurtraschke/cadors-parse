import json
import re
import urlparse
import urllib
from decimal import Decimal, setcontext, ExtendedContext

from SPARQLWrapper import SPARQLWrapper, JSON
from flask import g, current_app as app
from werkzeug import cached_property
from bson.son import SON

setcontext(ExtendedContext)


class Aerodromes(object):
    @cached_property
    def get_icao_re(self):
        icao_codes = g.mdb.aerodromes.find({'icao':{'$exists':True}},
                                           {'icao':1})
        
        tc_codes = g.mdb.aerodromes.find({'lid':{'$exists':True}},
                                         {'lid':1})

        codes = [c['icao'] for c in icao_codes] + [c['lid'] for c in tc_codes]

        re_string = r"\b(" + '|'.join(codes) + r")\b"
        aerodromes_re = re.compile(re_string)
        return aerodromes_re

    """
    @cached_property
    def get_iata_re(self):
        if 'iata_re_cache' not in g.db:
            #Blacklist likely false positives; this is not an ideal solution.
            #Some of these are listed because they conflict with ICAO airline designators.
            #It would help to have a database of airline designators, but that wouldn't help disambiguate
            #between ICAO airline designators and IATA airport codes.
            blacklist = ["iata:" + c for c in g.db.smembers('iata_blacklist')]
            re_string = r"\b(" + '|'.join([re.escape(c.lstrip("iata:")) for c in g.db.smembers('iata_codes') if c not in blacklist]) + r")\b"
            g.db.setex('iata_re_cache', re_string, 3600)
        aerodromes_re = re.compile(g.db['iata_re_cache'])
        return aerodromes_re
    """
aerodromes_re = Aerodromes()


def replace_aerodromes(text, link_function):
    substitutions = {}

    def process_matches(matches, lookup):
        for match in matches:
            title = match.group()
            result = lookup(match.group())
            latitude = str(result['location']['latitude'])
            longitude = str(result['location']['longitude'])
            coordinates = latitude + ', ' + longitude
            title = u"{0} ({1})".format(result['name'],
                                        coordinates)
            substitutions[match] = link_function(result['airport'],
                                                 match.group(), title, 
                                                 coordinates={
                    'latitude': latitude,
                    'longitude': longitude})

    icao_matches = aerodromes_re.get_icao_re.finditer(text)
    process_matches(icao_matches, lambda code: lookup(code))
    #iata_matches = aerodromes_re.get_iata_re.finditer(text)
    #process_matches(iata_matches, lambda id: lookup('iata:' + id))

    return substitutions


def lookup(code):
    return g.mdb.aerodromes.find_one({"$or": [{"icao": code},
                                              {"lid": code},
                                              {"iata": code}, 
                                              {"faa": code}]})
    
    

def fix_coord(value):
    precision = Decimal('0.000001')
    input = Decimal(str(value))
    return float(input.quantize(precision))

def import_blacklist():
    g.db.delete('iata_blacklist')
    g.db.delete('iata_re_cache')
    with app.open_resource('cadorslib/filters/blacklist.txt') as blacklist:
        for line in blacklist:
            line = line.strip()
            if not line.startswith('#') and len(line) == 3:
                g.db.sadd('iata_blacklist', line)

def fetch_aerodromes():
    with app.open_resource("cadorslib/filters/dbpedia_query.rq") as queryfile:
        query = queryfile.read()

    limit = 500

    def fetchResults(offset):
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(query % (offset, limit))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            values = dict([(key, value['value']) for key, value in result.items()])
            values['location'] = SON()
            values['location']['longitude'] = fix_coord(values['longitude'])
            values['location']['latitude'] = fix_coord(values['latitude'])
            
            del values['longitude']
            del values['latitude']
            if 'name' not in values:
                values['name'] = urllib.unquote(urlparse.urlparse(values['airport']).path.decode('utf-8').split('/')[-1]).replace('_', ' ')

            g.mdb.aerodromes.insert(values)

        if len(results["results"]["bindings"]) == limit:
            fetchResults(offset + limit)

    fetchResults(0)
