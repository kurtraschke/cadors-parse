import json

from sqlalchemy.orm.exc import NoResultFound
from geoalchemy import WKTSpatialElement

from cadorsfeed.models import Aerodrome
from cadorsfeed import db


def import_aerodromes(json_filename):
    with open(json_filename) as json_file:
        aerodromes = json.load(json_file)

    to_remove = db.session.query(Aerodrome)
    to_remove = to_remove.filter(~Aerodrome.airport.in_(aerodromes.keys()))
    to_remove = to_remove.all()

    for aerodrome in to_remove:
        db.session.delete(aerodrome)
    db.session.commit()

    for aerodrome_data in aerodromes.values():
        if aerodrome_data.get('iata_duplicate', False):
            aerodrome_data['iata'] = None
        try:
            aerodrome = db.session.query(Aerodrome)
            aerodrome = aerodrome.filter(
                Aerodrome.airport == aerodrome_data['airport']).one()
        except NoResultFound:
            aerodrome = Aerodrome()
            aerodrome.airport = aerodrome_data['airport']

        wkt = "POINT(%s %s)" % (aerodrome_data['location']['coordinates'][0],
                                aerodrome_data['location']['coordinates'][1])
        aerodrome.location = WKTSpatialElement(wkt)
        for field in ['icao', 'iata', 'faa', 'lid']:
            value = aerodrome_data.get(field, None)
            setattr(aerodrome, field, value)
        aerodrome.name = aerodrome_data['name']

        db.session.add(aerodrome)

    db.session.commit()
