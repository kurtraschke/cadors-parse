import html5lib
from html5lib import treebuilders
from lxml import etree
from os import path

from functions import extensions
from utils import application

def parse(input_doc):
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(input_doc)
    transform = application.transform
    result_tree = transform(etree_document)
    output_doc = etree.tostring(result_tree, encoding=unicode,
                                pretty_print=True)
    return output_doc

def make_transform():
    stylesheet = path.join(path.dirname(__file__), 'format.xsl')
    xslt_doc = etree.parse(stylesheet)
    transform = etree.XSLT(xslt_doc, extensions=extensions)
    return transform
