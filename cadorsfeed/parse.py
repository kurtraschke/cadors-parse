import html5lib
from lxml import etree
from os import path
from datetime import datetime
from pyrfc3339 import generate

from functions import extensions


def parse(input_doc):
    parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(input_doc)

    atom_stylesheet = path.join(path.dirname(__file__), 'format.xsl')
    atom_xslt_doc = etree.parse(atom_stylesheet)
    atom_transform = etree.XSLT(atom_xslt_doc, extensions=extensions)

    ts = etree.XSLT.strparam(generate(datetime.utcnow(), accept_naive=True))
    atom_result_tree = atom_transform(etree_document, ts=ts)

    atom_output = etree.tostring(atom_result_tree, encoding=unicode,
                                 pretty_print=True)

    html_xslt_doc = etree.parse(path.join(path.dirname(__file__),
                                          'static', 'html.xsl'))
    html_transform = etree.XSLT(html_xslt_doc)
    html_result_tree = html_transform(atom_result_tree)
    html_output = etree.tostring(html_result_tree, encoding=unicode,
                                 pretty_print=True, method="html")
    return {'output': atom_output, 'output_html': html_output}
