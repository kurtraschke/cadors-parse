import json
import re
import urlparse
import urllib
from SPARQLWrapper import SPARQLWrapper, JSON
from decimal import Decimal, setcontext, ExtendedContext
from flask import g
from werkzeug import cached_property

setcontext(ExtendedContext)


class Aerodromes(object):
    @cached_property
    def get_icao_re(self):
        if 'icao_re_cache' not in g.db:
            re_string = r"\b(" + '|'.join([re.escape(c.lstrip("icao:")) for c in g.db.smembers('icao')]) + r")\b"
            g.db.setex('icao_re_cache', re_string, 3600)
        aerodromes_re = re.compile(g.db['icao_re_cache'])
        return aerodromes_re

    @cached_property
    def get_iata_re(self):
        if 'iata_re_cache' not in g.db:
            #Blacklist likely false positives
            blacklist = ["iata:" + c for c in ('ATC', 'SMS', 'DME')]
            re_string = r"\b(" + '|'.join([re.escape(c.lstrip("iata:")) for c in g.db.smembers('iata') if c not in blacklist]) + r")\b"
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
    process_matches(icao_matches, lookup_icao)
    iata_matches = aerodromes_re.get_iata_re.finditer(text)
    process_matches(iata_matches, lambda id: lookup_icao(g.db['iata:' + id]))

    return substitutions


def lookup_icao(id):
    hashkey = "icao:" + id
    keys = ['latitude', 'longitude', 'name', 'airport']
    values = g.db.hmget(hashkey, keys)
    out = dict(zip(keys, values))
    return out


def round(value):
    precision = Decimal('0.000001')
    input = Decimal(str(value))
    return str(input.quantize(precision))


def fetch_aerodromes():
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addCustomParameter("default-graph-uri", "http://dbpedia.org")
    sparql.setQuery("""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX grs: <http://www.georss.org/georss/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?name ?icao ?iata ?coordinates ?airport
    WHERE {
        ?airport rdf:type <http://dbpedia.org/ontology/Airport> .
        ?airport dbo:icaoLocationIdentifier ?icao .
        FILTER regex(?icao, "^[A-Z0-9]{4}$")
        ?airport dbo:iataLocationIdentifier ?iata .
        FILTER regex(?iata, "^[A-Z0-9]{3}$")
        OPTIONAL {
            ?airport rdfs:label ?name
            FILTER ( lang(?name) = "en" )
        }
        ?airport grs:point ?coordinates .
    }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    g.db.delete('icao')
    g.db.delete('iata')

    for result in results["results"]["bindings"]:
        values = dict([(key, value['value']) for key, value in result.items()])
        (values['latitude'], values['longitude']) = values['coordinates'].split(' ')
        values['longitude'] = round(values['longitude'])
        values['latitude'] = round(values['latitude'])
        del values['coordinates']
        if 'name' not in values:
            values['name'] = urllib.unquote(urlparse.urlparse(values['airport']).path.decode('utf-8').split('/')[-1]).replace('_', ' ')

        key = "icao:" + values['icao']
        iatakey = "iata:" + values['iata']

        g.db.hmset(key, values)
        g.db.sadd('icao', key)
        g.db.set(iatakey, values['icao'])
        g.db.sadd('iata', iatakey)
