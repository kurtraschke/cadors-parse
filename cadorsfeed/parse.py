import html5lib
from lxml import etree
from os import path
from datetime import datetime
from pyrfc3339 import generate

from functions import extensions


def parse(input_doc):
    parser = html5lib.HTMLParser(
        tree=html5lib.treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(input_doc)
    stylesheet = path.join(path.dirname(__file__), 'format.xsl')
    xslt_doc = etree.parse(stylesheet)
    transform = etree.XSLT(xslt_doc, extensions=extensions)
    ts = etree.XSLT.strparam(generate(datetime.utcnow(), accept_naive=True))
    result_tree = transform(etree_document, ts=ts)
    output_doc = etree.tostring(result_tree, encoding=unicode,
                                pretty_print=True)
    return output_doc
