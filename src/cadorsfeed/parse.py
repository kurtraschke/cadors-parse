import html5lib
from lxml import etree
from os import path
from datetime import datetime
from pyrfc3339 import generate

from cadorsfeed.functions import extensions
from cadorsfeed import app


def parse(input_doc):
    parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(input_doc)

    with app.open_resource('static/format.xsl') as f:
        atom_xslt_doc = etree.parse(f)
    atom_transform = etree.XSLT(atom_xslt_doc, extensions=extensions)

    ts = etree.XSLT.strparam(generate(datetime.utcnow(), accept_naive=True))
    atom_result_tree = atom_transform(etree_document, ts=ts)

    atom_output = etree.tostring(atom_result_tree, encoding=unicode,
                                 pretty_print=True)

    with app.open_resource('static/html.xsl') as f:
        html_xslt_doc = etree.parse(f)
    html_transform = etree.XSLT(html_xslt_doc)
    html_result_tree = html_transform(atom_result_tree)
    html_output = etree.tostring(html_result_tree, encoding=unicode,
                                 pretty_print=True, method="html")
    return {'output': atom_output, 'output_html': html_output}
