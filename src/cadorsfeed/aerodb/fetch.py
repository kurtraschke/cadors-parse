import urlparse
import urllib
from decimal import Decimal, setcontext, ExtendedContext

from SPARQLWrapper import SPARQLWrapper, JSON
from flask import current_app as app
from geoalchemy import WKTSpatialElement
from sqlalchemy.exc import IntegrityError

from cadorsfeed.models import Aerodrome
from cadorsfeed import db

setcontext(ExtendedContext)


def fix_coord(value):
    precision = Decimal('0.000001')
    value_d = Decimal(str(value))
    return str(value_d.quantize(precision))


def fetch_aerodromes():
    with app.open_resource("aerodb/dbpedia_query.rq") as queryfile:
        query = queryfile.read()

    limit = 1000

    def fetchResults(offset):
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(query % (offset, limit))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            values = dict([(key, value['value']) for key, value \
                           in result.items()])
            values['longitude'] = fix_coord(values['longitude'])
            values['latitude'] = fix_coord(values['latitude'])

            if 'name' not in values:
                values['name'] = urllib.unquote(urlparse.urlparse(
                        values['airport']).path.decode(
                        'utf-8').split('/')[-1]).replace('_', ' ')

            store_aerodrome(values)

        if len(results["results"]["bindings"]) == limit:
            fetchResults(offset + limit)

    fetchResults(0)


def store_aerodrome(values):
    try:
        wkt = "POINT(%s %s)" % (values['longitude'], values['latitude'])
        values['location'] = WKTSpatialElement(wkt)
        del values['latitude']
        del values['longitude']
        aerodrome = Aerodrome(**values)
        db.session.add(aerodrome)
        db.session.commit()
    except IntegrityError, e:
        print "Duplicate aerodrome definition dropped:"
        print values
        print e
        db.session.rollback()
