import re
from lxml import etree

from geolucidate.functions import get_replacements

from cadorsfeed.filters.aerodromes import replace_aerodromes
from cadorsfeed.filters.link_cadors import replace_cadors_links
from cadorsfeed.filters.filter import make_link, make_span, do_filter


NSMAP = {'h': 'http://www.w3.org/1999/xhtml',
         'a': 'http://www.w3.org/2005/Atom',
         'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'}

def geolucidate_span(maplink):
    return make_span(maplink.original_string,
                     maplink.coordinates(", "),
                     coordinates={'latitude': maplink.lat_str,
                                  'longitude': maplink.long_str})



def process_narrative(narrative_block):
    paras = re.split(r'\n|(?:\*| ){4,}|_{4,}', narrative_block)
    div = etree.Element("{http://www.w3.org/1999/xhtml}div",
                        nsmap={'h': 'http://www.w3.org/1999/xhtml'})
    
    filters = [lambda text: get_replacements(text, geolucidate_span),
               lambda text: replace_aerodromes(text, make_link),
               lambda text: replace_cadors_links(text, make_link)]
    for paragraph in paras:
        if len(paragraph) == 0:
            continue
        p = etree.Element("{http://www.w3.org/1999/xhtml}p",
                          nsmap={'h': 'http://www.w3.org/1999/xhtml'})
        p.text = paragraph
        for filter in filters:
            p = do_filter(p, filter)
        div.append(p)
    return etree.tostring(div)
