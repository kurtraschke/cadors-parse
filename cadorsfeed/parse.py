import html5lib
from html5lib import treebuilders
from lxml import etree
from os import path

from functions import *

def parse(input_doc):
 
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"))
    etree_document = parser.parse(input_doc)
       
    ns = etree.FunctionNamespace('urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd')
    ns['fix_names'] = fix_names
    ns['fix_datetime'] = fix_datetime
    ns['produce_id'] = produce_id
    ns['content'] = content
    
    stylesheet = path.join(path.dirname(__file__), 'format.xsl')

    xslt_doc = etree.parse(stylesheet)
    
    transform = etree.XSLT(xslt_doc)
    
    result_tree = transform(etree_document)
    
    output_doc = etree.tostring(result_tree, pretty_print=True)
    return output_doc
