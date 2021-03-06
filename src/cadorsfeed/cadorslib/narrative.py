import re
from lxml import etree

from geolucidate.functions import get_replacements

from cadorsfeed.aerodb import replace_aerodromes
from cadorsfeed.cadorslib.filters.link_cadors import replace_cadors_links
from cadorsfeed.cadorslib.filters.filter import make_link, make_span, do_filter


NSMAP = {None: 'http://www.w3.org/1999/xhtml',
         #'a': 'http://www.w3.org/2005/Atom',
         'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
         'aero':'urn:uuid:1469bf5a-50a9-4c9b-813c-af19f9d6824d'}


def geolucidate_span(maplink):
    return make_span(maplink.original_string,
                     maplink.coordinates(", "),
                     coordinates={'latitude': maplink.lat_str,
                                  'longitude': maplink.long_str})


def process_narrative(narrative_block):
    paras = re.split(r'\n|(?:\*| ){4,}|_{4,}', narrative_block)
    div = etree.Element("{http://www.w3.org/1999/xhtml}div",
                        nsmap=NSMAP)

    filters = [lambda text: get_replacements(text, geolucidate_span),
               lambda text: replace_aerodromes(text, make_link),
               lambda text: replace_cadors_links(text, make_link)]
    for paragraph in paras:
        if len(paragraph) == 0:
            continue
        p = etree.Element("{http://www.w3.org/1999/xhtml}p",
                          nsmap=NSMAP)
        p.text = paragraph
        for filter_func in filters:
            p = do_filter(p, filter_func)
        div.append(p)

    return normalize_ns(div, nsmap=NSMAP)

def normalize_ns(root, **kwargs):
    new_root = etree.Element(root.tag, root.attrib, **kwargs)
    new_root[:] = root[:]
    return new_root
