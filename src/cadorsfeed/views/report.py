from urllib2 import URLError
from datetime import datetime
import time
import json

from flask import abort, request, redirect, url_for, g, make_response, session, flash, render_template, Module

import bson.json_util

from cadorsfeed.views.util import process_report_atom


report = Module(__name__)


@report.route('/report/<report>', defaults={'format':'html'})
@report.route('/report/<report>.<any(u"atom", u"json", u"html", u"kml"):format>')
def display_report(report, format):
    report = g.mdb.reports.find_one({'cadors_number': report})
    if report is None:
        abort(404)

    if format == 'atom':
        reports = process_report_atom([report])
        response = make_response(render_template('feed.xml', 
                                                 reports=reports))
        response.mimetype = "application/atom+xml"
    elif format == 'json':
        response = make_response(json.dumps({'report': report},
                                            indent=None if request.is_xhr else 2,
                                            default=bson.json_util.default))
        response.mimetype = "application/json"
    elif format == 'html':
        response = make_response(render_template('report.html',
                                                 reports=[report]))
    elif format == 'kml':
        response = make_response(render_template('kml.xml', report=report))
        response.mimetype = "application/vnd.google-earth.kml+xml"

    #response.last_modified = ...
    response.add_etag()
    response.make_conditional(request)
    return response

