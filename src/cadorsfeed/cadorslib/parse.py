import re
import datetime
from itertools import izip_longest

import html5lib
from lxml import etree
from bson.son import SON
from flask import g

from geolucidate.functions import cleanup, convert
from geolucidate.parser import parser_re

from cadorsfeed.cadorslib.xpath_functions import extensions
from cadorsfeed.cadorslib.narrative import process_narrative
from cadorsfeed.cadorslib.locations import LocationStore
from cadorsfeed.cadorslib.filters.aerodromes import aerodromes_re, lookup


NSMAP = {'h':'http://www.w3.org/1999/xhtml',
         'pyf':'urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd',
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
    for field, query in fields.iteritems():
        out[field] = node.xpath(query, namespaces=NSMAP,
                                extensions=extensions)
    return out

def make_queries(fields):
    out = {}
    for name, query in fields.iteritems():
        out[name] = "pyf:strip_nbsp(.//h:th[text()='%s']/following-sibling::h:td/h:strong/text())" % query
    return out

def make_datetime(date, time):
    if time == "":
        time = "0000 Z"
    return datetime.datetime.strptime(date+" "+time, "%Y-%m-%d %H%M Z")

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
                      etree_document.xpath('//h:div[@class = "widthFull" and contains(text(), "CADORS National Report dated")]',
                                           namespaces=NSMAP)[0].text).group()

    daily_report = {'date': datetime.datetime.strptime(header_date,
                                                       "%Y-%m-%d"),
                    'parse_timestamp': datetime.datetime.utcnow(),
                    'reports': parsed_reports
                    }

    return daily_report

def parse_report(report):
    fields = {'cadors_number': 'Cadors Number:',
              'region': 'Reporting Region:',
              'type': 'Occurrence Type:',
              'date': 'Occurrence Date:',
              'time': 'Occurrence Time:',
              'day_night': 'Day Or Night:',
              'fatalities': 'Fatalities:',
              'injuries': 'Injuries:',
              'tclid': 'Canadian Aerodrome ID:',
              'aerodrome_name': 'Aerodrome Name:',
              'location': 'Occurrence Location:',
              'province': 'Province:',
              'country': 'Country:',
              'world_area': 'World Area:',
              'reported_by': 'Reported By:',
              'nav_canada_aor': 'AOR Number:',
              'tsb_class': 'TSB Class Of Investigation:',
              'tsb_number': 'TSB Occurrence No:'}

    fields = make_queries(fields)

    fields['categories'] = ".//h:fieldset/h:legend/h:strong[contains(text(),'Event Information')]/../following-sibling::h:table//h:strong/text()"

    report_data = extractor(report, fields)
    report_data['narrative'] = []
    report_data['aircraft'] = []

    narrative_parts = report.xpath(".//h:fieldset/h:legend/h:strong[contains(text(),'Detail Information')]/../following-sibling::h:table",
                                 namespaces=NSMAP, extensions=extensions)

    narrative_fields = {'name': 'User Name:',
                        'date': 'Date:',
                        'further_action': 'Further Action Required:',
                        'opi': 'O.P.I.:',
                        'narrative': 'Narrative:'}

    for narrative_part in grouper(5, narrative_parts):
        narrative_data = extractor(narrative_part,
                                  make_queries(narrative_fields))
        report_data['narrative'].append(narrative_data)

    aircraft_parts = report.xpath(".//h:fieldset/h:legend/h:strong[contains(text(),'Aircraft Information')]/../following-sibling::h:table",
                                  namespaces=NSMAP, extensions=extensions)

    aircraft_fields = {'flight_number': 'Flight #:',
                       'category': 'Aircraft Category:',
                       'reg_country': 'Country of Registration:',
                       'make': 'Make:',
                       'model': 'Model:',
                       'year': 'Year Built:',
                       'amateur_built': 'Amateur Built:',
                       'engine_make': 'Engine Make:',
                       'engine_model': 'Engine Model:',
                       'engine_type': 'Engine Type:',
                       'gear_type': 'Gear Type:',
                       'flight_phase': 'Phase of Flight:',
                       'damage': 'Damage:',
                       'owner': 'Owner:',
                       'operator': 'Operator:',
                       'operator_type': 'Operator Type:'}

    for aircraft_part in grouper(9, aircraft_parts):
        aircraft_data = extractor(aircraft_part,
                                  make_queries(aircraft_fields))
        report_data['aircraft'].append(aircraft_data)

    #All of the extraction is done; on to formatting and cleanup.

    report_data['timestamp'] = make_datetime(report_data['date'],
                                             report_data['time'])
    del report_data['date']
    del report_data['time']
    report_data['fatalities'] = int(report_data['fatalities'])
    report_data['injuries'] = int(report_data['injuries'])

    locations = LocationStore()

    if report_data['tclid'] != '':
        #try to do a db lookup
        data = lookup(report_data['tclid'])
        if data is not None:
            locations.add(data['location']['latitude'],
                          data['location']['longitude'],
                          data['name'],
                          data['airport'])

    if report_data['location'] != '':
        location = report_data['location']
        #Apply geolucidate and the aerodromes RE
        match = aerodromes_re.get_icao_re.search(location)
        if match:
            data = lookup(match.group())
            locations.add(data['location']['latitude'],
                          data['location']['longitude'],
                          data['name'],
                          data['airport'])
        match = parser_re.search(location)
        if match:
            (latitude, longitude) = convert(*cleanup(match.groupdict()))

            locations.add(latitude,
                          longitude,
                          match.group())

    for narrative_part in report_data['narrative']:
        name = narrative_part['name']
        (last, first) = name.split(", ")
        narrative_part['name'] = first + " " + last
        narrative_part['date'] = datetime.datetime.strptime(narrative_part['date'],
                                                            "%Y-%m-%d")

        narrative_part['parsed_html'] = process_narrative(narrative_part['narrative'])
        #do the location extraction here
        root = etree.fromstring(narrative_part['parsed_html'])
        elements = root.xpath("//*[@class='geolink' and @geo:lat and @geo:long]",
                              namespaces=NSMAP)
        for element in elements:
            longitude = element.attrib['{http://www.w3.org/2003/01/geo/wgs84_pos#}long']
            latitude = element.attrib['{http://www.w3.org/2003/01/geo/wgs84_pos#}lat']

            name = element.attrib['title']
            if 'href' in element.attrib:
                url = element.attrib['href']
            else:
                url = None
            locations.add(latitude, longitude, name, url)

    for aircraft_part in report_data['aircraft']:
        if aircraft_part['flight_number'] != "":
            match = re.match("([A-Z]{2,4})([0-9]{1,4}M?)",
                             aircraft_part['flight_number'])
            if match:
                parsed_flight = {'operator': match.group(1),
                                 'flight': match.group(2)}
                aircraft_part['flight_number_parsed'] = parsed_flight


    report_data['locations'] = locations.to_list(report_data['cadors_number'])

    return report_data
