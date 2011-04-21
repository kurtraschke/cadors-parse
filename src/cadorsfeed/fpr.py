import re
import uuid
from copy import deepcopy
from datetime import datetime

from lxml import etree
from lxml.html import xhtml_to_html

from geoalchemy import WKTSpatialElement

from geolucidate.functions import _cleanup, _convert
from geolucidate.parser import parser_re

from cadorsfeed import db
from cadorsfeed.models import DailyReport, CadorsReport, ReportCategory
from cadorsfeed.models import Aircraft, NarrativePart, Location, LocationRef
from cadorsfeed.cadorslib.xpath_functions import extensions
from cadorsfeed.cadorslib.narrative import process_narrative, normalize_ns
from cadorsfeed.cadorslib.locations import LocationStore
from cadorsfeed.aerodb import aerodromes_re, lookup


NSMAP = {'h': 'http://www.w3.org/1999/xhtml',
         'pyf': 'urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd',
         'a': 'http://www.w3.org/2005/Atom',
         'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
         'aero':'urn:uuid:1469bf5a-50a9-4c9b-813c-af19f9d6824d'}


def make_datetime(date, time):
    if time is None:
        time = "0000 Z"
    return datetime.strptime(date + " " + time, "%Y-%m-%d %H%M Z")

def clean_html(tree):
    mytree = deepcopy(tree)
    for elem in mytree.iter():
        for attr, val in elem.attrib.iteritems():
            if attr.startswith('{'):
                del elem.attrib[attr]

    xhtml_to_html(mytree)
    return etree.tostring(normalize_ns(mytree), method="html",
                          encoding=unicode)


def format_parsed_report(parsed_report):
    report = CadorsReport.query.get(
        parsed_report['cadors_number']) or CadorsReport(uuid=uuid.uuid4())
    
    
    parsed_report['timestamp'] = make_datetime(parsed_report['date'],
                                               parsed_report['time'])
    del parsed_report['date']
    del parsed_report['time']

    primary_locations = set()
    other_locations = set()

    if parsed_report['tclid'] != '':
        #try to do a db lookup
        data = lookup(parsed_report['tclid'])
        if data is not None:
            primary_locations.add(data)

    if parsed_report['location'] != '':
        location = parsed_report['location']
        #Apply geolucidate and the aerodromes RE
        match = aerodromes_re.get_icao_re.search(location)
        if match:
            data = lookup(match.group())
            primary_locations.add(data)

        match = parser_re.search(location)
        if match:
            (latitude, longitude) = _convert(*_cleanup(match.groupdict()))

            location = make_location(latitude, longitude)
            location.name = match.group()

            primary_locations.add(location)

    for narrative_part in parsed_report['narrative']:
        narrative_tree = process_narrative(narrative_part['narrative_text'])

        narrative_part['narrative_html'] = clean_html(narrative_tree)
        narrative_part['narrative_xml'] = etree.tostring(narrative_tree,
                                                         method="xml",
                                                         encoding=unicode)

        #do the location extraction here        
        #parse out geolinks
        elements = narrative_tree.xpath(
            "//*[@class='geolink' and @geo:lat and @geo:long]",
            namespaces=NSMAP)
        for element in elements:
            longitude = element.attrib[
                '{http://www.w3.org/2003/01/geo/wgs84_pos#}long']
            latitude = element.attrib[
                '{http://www.w3.org/2003/01/geo/wgs84_pos#}lat']

            name = element.attrib['title']
            location = make_location(latitude, longitude)
            location.name = name
            other_locations.add(location)
        #parse out aerodrome links
        elements = narrative_tree.xpath(
            "//*[@class='aerolink' and @aero:code]",
            namespaces=NSMAP)
        for element in elements:
            code = element.attrib[
                '{urn:uuid:1469bf5a-50a9-4c9b-813c-af19f9d6824d}code']
            other_locations.add(lookup(code))

    for aircraft_part in parsed_report['aircraft']:
        if aircraft_part['flight_number'] is not None:
            match = re.match("([A-Z]{2,4})([0-9]{1,4})M?",
                             aircraft_part['flight_number'])
            if match:
                aircraft_part['flight_number_operator'] = match.group(1)
                aircraft_part['flight_number_flight'] = match.group(2)

    report.categories = []
    report.aircraft = []
    report.narrative_parts = []
    report.locations = []

    for category in parsed_report['categories']:
        report.categories.append(ReportCategory(text=category))
    del parsed_report['categories']

    for aircraft_part in parsed_report['aircraft']:
        report.aircraft.append(Aircraft(**aircraft_part))
    del parsed_report['aircraft']
    
    for narrative_part in parsed_report['narrative']:
        report.narrative_parts.append(NarrativePart(**narrative_part))
    del parsed_report['narrative']

    for location in primary_locations:
        locref = LocationRef(report=report, location=location,
                             primary=True)
        db.session.add(locref)

    other_locations -= primary_locations

    for location in other_locations:
        locref = LocationRef(report=report, location=location,
                             primary=False)
        db.session.add(locref)
    

    for key, value in parsed_report.iteritems():
        setattr(report, key, value)

    return report
    
    
def make_location(latitude, longitude):
    wkt = "POINT(%s %s)" % (longitude,
                            latitude)
    point = WKTSpatialElement(wkt)
    location = Location(location=point)
    return location
