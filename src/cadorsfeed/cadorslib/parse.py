import re
from datetime import datetime
from itertools import izip_longest

import html5lib
from lxml import etree
#from bson.son import SON
#from flask import g

from geolucidate.functions import cleanup, convert
from geolucidate.parser import parser_re

from cadorsfeed.cadorslib.xpath_functions import extensions
from cadorsfeed.cadorslib.narrative import process_narrative
from cadorsfeed.cadorslib.locations import LocationStore
from cadorsfeed.aerodb import aerodromes_re, lookup


NSMAP = {'h': 'http://www.w3.org/1999/xhtml',
         'pyf': 'urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd',
         'a': 'http://www.w3.org/2005/Atom',
         'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'}


def grouper(n, iterable):
    args = [iter(iterable)] * n
    return [group(l) for l in izip_longest(fillvalue=None, *args)]


def group(elements):
    element = etree.Element("{http://www.w3.org/1999/xhtml}p",
                            nsmap={'h': 'http://www.w3.org/1999/xhtml'})
    element.extend(elements)
    return element


def extractor(node, fields):
    out = {}
    for field, specification in fields.iteritems():
        (query, translator) = specification
        data = node.xpath(query, namespaces=NSMAP,
                                extensions=extensions)
        data = translator(data)
        if translator is str or translator is unicode:
            if len(data) == 0:
                data = None
        out[field] = data
    return out


def q(query):
    return "pyf:strip_nbsp(.//h:th[text()='%s']/" \
        "following-sibling::h:td/h:strong/text())" % query


def make_datetime(date, time):
    if time is None:
        time = "0000 Z"
    return datetime.strptime(date + " " + time, "%Y-%m-%d %H%M Z")


def safe_int(value):
    try:
        return int(value)
    except ValueError:
        return None


def fix_name(name):
    (last, first) = name.split(", ")
    return u"%s %s" % (first, last)


def narrative_date(date_string):
    return datetime.strptime(date_string, "%Y-%m-%d")


def unicode_list(items):
    return [unicode(item) for item in items]


def parse_daily_report(report_file):
    parser = html5lib.HTMLParser(
        tree=html5lib.treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(report_file, encoding="utf-8")

    reports = etree_document.xpath("//h:div[@class = 'pagebreak']",
                                   namespaces=NSMAP)

    parsed_reports = []

    for report_xml in reports:
        report_data = parse_report(report_xml)
        parsed_reports.append(report_data)

    header_date = re.search("\d\d\d\d-\d\d-\d\d",
                            etree_document.xpath(
            '//h:div[@class = "widthFull" and ' \
                'contains(text(), "CADORS National Report dated")]',
            namespaces=NSMAP)[0].text).group()

    daily_report = {'date': datetime.strptime(header_date,
                                              "%Y-%m-%d"),
                    'parse_timestamp': datetime.utcnow(),
                    'reports': parsed_reports}

    return daily_report


def parse_report(report):
    fields = {'cadors_number': (q('Cadors Number:'), str),
              'region': (q('Reporting Region:'), unicode),
              'occurrence_type': (q('Occurrence Type:'), unicode),
              'date': (q('Occurrence Date:'), str),
              'time': (q('Occurrence Time:'), str),
              'day_night': (q('Day Or Night:'), unicode),
              'fatalities': (q('Fatalities:'), safe_int),
              'injuries': (q('Injuries:'), safe_int),
              'tclid': (q('Canadian Aerodrome ID:'), str),
              'aerodrome_name': (q('Aerodrome Name:'), unicode),
              'location': (q('Occurrence Location:'), unicode),
              'province': (q('Province:'), unicode),
              'country': (q('Country:'), unicode),
              'world_area': (q('World Area:'), unicode),
              'reported_by': (q('Reported By:'), unicode),
              'nav_canada_aor': (q('AOR Number:'), unicode),
              'tsb_class': (q('TSB Class Of Investigation:'), safe_int),
              'tsb_number': (q('TSB Occurrence No:'), unicode)}

    fields['categories'] = (
        ".//h:fieldset/h:legend/h:strong[contains(text()," \
            "'Event Information')]/../following-sibling::h:table//" \
            "h:strong/text()", unicode_list)

    report_data = extractor(report, fields)
    report_data['narrative'] = []
    report_data['aircraft'] = []

    narrative_parts = report.xpath(
        ".//h:fieldset/h:legend/h:strong[contains(text()," \
            "'Detail Information')]/../following-sibling::h:table",
        namespaces=NSMAP, extensions=extensions)

    narrative_fields = {'author_name': (q('User Name:'), fix_name),
                        'date': (q('Date:'), narrative_date),
                        'further_action': (q('Further Action Required:'),
                                             unicode),
                        'opi': (q('O.P.I.:'), unicode),
                        'narrative_text': (q('Narrative:'), unicode)}

    for narrative_part in grouper(5, narrative_parts):
        narrative_data = extractor(narrative_part,
                                   narrative_fields)
        report_data['narrative'].append(narrative_data)

    aircraft_parts = report.xpath(
        ".//h:fieldset/h:legend/h:strong[contains(text()," \
            "'Aircraft Information')]/../following-sibling::h:table",
        namespaces=NSMAP, extensions=extensions)

    aircraft_fields = {'flight_number': (q('Flight #:'), unicode),
                       'category': (q('Aircraft Category:'), unicode),
                       'reg_country': (q('Country of Registration:'), unicode),
                       'make': (q('Make:'), unicode),
                       'model': (q('Model:'), unicode),
                       'year': (q('Year Built:'), safe_int),
                       'amateur_built': (q('Amateur Built:'), unicode),
                       'engine_make': (q('Engine Make:'), unicode),
                       'engine_model': (q('Engine Model:'), unicode),
                       'engine_type': (q('Engine Type:'), unicode),
                       'gear_type': (q('Gear Type:'), unicode),
                       'flight_phase': (q('Phase of Flight:'), unicode),
                       'damage': (q('Damage:'), unicode),
                       'owner': (q('Owner:'), unicode),
                       'operator': (q('Operator:'), unicode),
                       'operator_type': (q('Operator Type:'), unicode)}

    for aircraft_part in grouper(9, aircraft_parts):
        aircraft_data = extractor(aircraft_part,
                                  aircraft_fields)
        report_data['aircraft'].append(aircraft_data)

    #All of the extraction is done; on to formatting and cleanup.

    report_data['timestamp'] = make_datetime(report_data['date'],
                                             report_data['time'])
    del report_data['date']
    del report_data['time']

    locations = LocationStore()

    if report_data['tclid'] != '':
        #try to do a db lookup
        data = lookup(report_data['tclid'])
        if data is not None:
            locations.add(data.latitude,
                          data.longitude,
                          data.name,
                          data.airport,
                          True)

    if report_data['location'] != '':
        location = report_data['location']
        #Apply geolucidate and the aerodromes RE
        match = aerodromes_re.get_icao_re.search(location)
        if match:
            data = lookup(match.group())
            locations.add(data.latitude,
                          data.longitude,
                          data.name,
                          data.airport,
                          True)
        match = parser_re.search(location)
        if match:
            (latitude, longitude) = convert(*cleanup(match.groupdict()))

            locations.add(latitude,
                          longitude,
                          match.group(),
                          primary=True)

    for narrative_part in report_data['narrative']:
        narrative_part['narrative_html'] = process_narrative(
            narrative_part['narrative_text'])
        #do the location extraction here
        root = etree.fromstring(narrative_part['narrative_html'])
        elements = root.xpath(
            "//*[@class='geolink' and @geo:lat and @geo:long]",
            namespaces=NSMAP)
        for element in elements:
            longitude = element.attrib[
                '{http://www.w3.org/2003/01/geo/wgs84_pos#}long']
            latitude = element.attrib[
                '{http://www.w3.org/2003/01/geo/wgs84_pos#}lat']

            name = element.attrib['title']
            url = element.attrib['href'] if 'href' in element.attrib else None
            locations.add(latitude, longitude, name, url)

    for aircraft_part in report_data['aircraft']:
        if aircraft_part['flight_number'] is not None:
            match = re.match("([A-Z]{2,4})([0-9]{1,4})M?",
                             aircraft_part['flight_number'])
            if match:
                aircraft_part['flight_number_operator'] = match.group(1)
                aircraft_part['flight_number_flight'] = match.group(2)

    report_data['locations'] = locations.to_list()

    return report_data
