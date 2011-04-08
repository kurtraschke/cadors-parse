import json

from flask import request, redirect, make_response, render_template, Module
from flask import current_app as app
from pyrfc3339 import generate

from cadorsfeed.views.util import process_report_atom, json_default, render_list
from cadorsfeed.models import CadorsReport
from cadorsfeed import modified_url_for

report = Module(__name__)


@report.route('/reports/', defaults={'page': 1, 'format':'html'})
@report.route('/reports/<int:page>.<any(u"atom", u"json", u"html"):format>')
def display_report_list(page, format):
    pagination = CadorsReport.query.paginate(page)
    title = "Reports"
    return render_list(pagination, title, format)


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
        response = make_response(
            render_template('report.html',
                            report=report,
                            google_maps_key=app.config['GOOGLE_MAPS_KEY']))
    elif format == 'kml':
        response = make_response(render_template('kml.xml', report=report))
        response.mimetype = "application/vnd.google-earth.kml+xml"
        
    response.last_modified = report.last_updated
    return prepare_response(response, 43200)

@report.route('/report/<report>/original')
def redirect_original(report):
    report = CadorsReport.query.get_or_404(report)

    return redirect("http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/qs.aspx?lang=eng&cadorsno=%s" % report.cadors_number)
