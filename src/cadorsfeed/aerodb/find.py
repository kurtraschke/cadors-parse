import re

from werkzeug import cached_property

from cadorsfeed.models import Aerodrome
from cadorsfeed.aerodb import lookup
from cadorsfeed import db

class Aerodromes(object):
    @cached_property
    def get_icao_re(self):
        icao_codes = db.session.query(Aerodrome.icao).filter(
            Aerodrome.icao != None).all()

        tc_codes = db.session.query(Aerodrome.tclid).filter(
            Aerodrome.tclid != None).all()
        
        codes = [c for (c,) in icao_codes] + [c for (c,) in tc_codes]

        re_string = r"\b(" + '|'.join(codes) + r")\b"
        aerodromes_re = re.compile(re_string)
        return aerodromes_re


    @cached_property
    def get_iata_re(self):
        iata_codes = db.session.query(Aerodrome.iata).filter(
            Aerodrome.iata != None).filter(Aerodrome.blacklist == False).all()

        faa_codes = db.session.query(Aerodrome.faa).filter(
            Aerodrome.faa != None).filter(Aerodrome.blacklist == False).all()
        
        codes = [c for (c,) in iata_codes] + [c for (c,) in faa_codes]

        re_string = r"\b(" + '|'.join(codes) + r")\b"
        aerodromes_re = re.compile(re_string)
        return aerodromes_re


aerodromes_re = Aerodromes()

def replace_aerodromes(text, link_function):
    substitutions = {}

    def process_matches(matches, lookup):
        for match in matches:
            title = match.group()
            result = lookup(match.group())
            latitude = str(result.latitude)
            longitude = str(result.longitude)
            coordinates = latitude + ', ' + longitude
            title = u"{0} ({1})".format(result.name,
                                        coordinates)
            substitutions[match] = link_function(result.airport,
                                                 match.group(), title, 
                                                 coordinates={
                    'latitude': latitude,
                    'longitude': longitude})

    icao_matches = aerodromes_re.get_icao_re.finditer(text)
    process_matches(icao_matches, lambda code: lookup(code))
    iata_matches = aerodromes_re.get_iata_re.finditer(text)
    process_matches(iata_matches, lambda code: lookup(code))

    return substitutions
