from sqlalchemy import or_
from cadorsfeed.models import Aerodrome

def lookup(code):
    if code is None:
        return None
    aerodrome = Aerodrome.query.filter(or_(Aerodrome.icao == code,
                                           Aerodrome.iata == code,
                                           Aerodrome.faa == code,
                                           Aerodrome.tclid == code)).first()
    return aerodrome
