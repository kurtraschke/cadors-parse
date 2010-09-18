import html5lib
from html5lib import treebuilders
from lxml import etree
from os import path
from datetime import datetime
from pyrfc3339 import generate

from functions import extensions
from utils import application

def parse(input_doc):
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(input_doc)
    transform = application.transform
    ts = etree.XSLT.strparam(generate(datetime.utcnow(), accept_naive=True))
    result_tree = transform(etree_document, ts=ts)
    output_doc = etree.tostring(result_tree, encoding=unicode,
                                pretty_print=True)
    return output_doc

def make_transform():
    stylesheet = path.join(path.dirname(__file__), 'format.xsl')
    xslt_doc = etree.parse(stylesheet)
    transform = etree.XSLT(xslt_doc, extensions=extensions)
    return transform

def generate_html(input_doc):
    xslt_doc = etree.parse(path.join(path.dirname(__file__),
                                     'static', 'html.xsl'))
    transform = etree.XSLT(xslt_doc)
    input_tree = etree.fromstring(input_doc)
    result_tree = transform(input_tree)
    output_doc = etree.tostring(result_tree, encoding=unicode,
                                pretty_print=True, method="html")
    return output_doc
