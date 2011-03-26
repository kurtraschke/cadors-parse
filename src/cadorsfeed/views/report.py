import json

from flask import request, make_response, render_template, Module
from pyrfc3339 import generate

from cadorsfeed.views.util import process_report_atom, json_default
from cadorsfeed.models import CadorsReport

report = Module(__name__)


@report.route('/reports/', defaults={'page': 1})
@report.route('/reports/<int:page>')
def display_report_list(page):

    pagination = CadorsReport.query.paginate(page)

    return render_template('list.html', reports=pagination.items,
                           pagination=pagination)


@report.route('/report/<report>', defaults={'format': 'html'})
@report.route(
    '/report/<report>.<any(u"atom", u"json", u"html", u"kml"):format>')
def display_report(report, format):
    report = CadorsReport.query.get_or_404(report)

    if format == 'atom':
        reports = process_report_atom([report])
        feed_timestamp = generate(report.last_updated, accept_naive=True)
        response = make_response(
            render_template('feed.xml',
                            reports=reports,
                            feed_timestamp=feed_timestamp))
        response.mimetype = "application/atom+xml"
    elif format == 'json':
        response = make_response(json.dumps(
                {'report': report},
                indent=None if request.is_xhr else 2,
                default=json_default))
        response.mimetype = "application/json"
    elif format == 'html':
        response = make_response(render_template('report.html',
                                                 reports=[report]))
    elif format == 'kml':
        response = make_response(render_template('kml.xml', report=report))
        response.mimetype = "application/vnd.google-earth.kml+xml"

    response.add_etag()
    response.make_conditional(request)
    return response
