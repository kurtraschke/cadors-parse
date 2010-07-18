
import html5lib
from html5lib import treebuilders
from lxml import etree
import re
from pyrfc3339 import generate
import datetime
import shelve
import uuid

f = open("rpt.html")
parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"))
etree_document = parser.parse(f)

def stripout(list):
    assert len(list) == 1
    return list[0]

def strip_nbsp(string):
    return string.rstrip(u'\xa0')

def fix_name(name):
    name = strip_nbsp(name)
    (last, first) = name.split(", \n")
    return first + " " + last

def elementify(string):
    element = etree.Element("{http://www.w3.org/1999/xhtml}p")
    element.text = string
    return element

def fix_names(context, names):
    return [elementify(s) for s in set([fix_name(name) for name in names])]

def fix_datetime(context, date, time):
    datere = re.compile(r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})")
    dateparts = datere.search(strip_nbsp(stripout(date))).groupdict()

    timere = re.compile(r"(?P<hour>[0-9]{2})(?P<minute>[0-9]{2}) Z")
    result = timere.search(strip_nbsp(stripout(time)))
    if result:
        timeparts = result.groupdict()
    else:
        timeparts = {'hour':0,'minute':0}

    ts = datetime.datetime(int(dateparts['year']),
                           int(dateparts['month']),
                           int(dateparts['day']),
                           int(timeparts['hour']),
                           int(timeparts['minute']))

    return generate(ts, accept_naive=True)

def produce_id(context, cadors_number):
    s = shelve.open('id_map.db', writeback=True)
    
    cadors_number = stripout(cadors_number)

    if not cadors_number in s:
        s[cadors_number] = uuid.uuid4()

    return s[cadors_number].urn

def content(context, content_list):
    out = []
    for block in content_list:
        paras = block.split('\n\n')
        for p in paras:
            if p:
                out.append(elementify(strip_nbsp(p)))
    
    return out


ns = etree.FunctionNamespace('http://www.kurtraschke.com/functions')
ns.prefix = 'pyf'
ns['fix_names'] = fix_names
ns['fix_datetime'] = fix_datetime
ns['produce_id'] = produce_id
ns['content'] = content

xslt_doc = etree.parse("format.xsl")

transform = etree.XSLT(xslt_doc)

result_tree = transform(etree_document)

#print etree.tostring(result_tree, pretty_print=True)

import sys
result_tree.write_c14n(sys.stdout)

"""
from lxml.cssselect import CSSSelector

sel = CSSSelector('h|div.pagebreak', namespaces={'h':"http://www.w3.org/1999/xhtml"})

for e in sel(etree_document):
    print 'foo'
"""
