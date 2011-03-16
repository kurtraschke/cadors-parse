from datetime import datetime
import json

from flask import abort, request, redirect, url_for, g
from flask import make_response, render_template, send_file, Module
from flask import current_app as app
import bson.json_util

from cadorsfeed.views.util import process_report_atom

daily_report = Module(__name__)

"""
@feeds.route('/report/latest/', defaults={'format': 'atom'})
@feeds.route('/report/latest/<any(u"atom", u"html"):format>')
def latest_report(format):
    if 'latest' in g.db:
        latestDate = g.db['latest']
    else:
        try:
            latestDate = fetchLatest()
            g.db.setex('latest', latestDate, 60 * 60 * 12)
        except Exception:
            raise

    (year, month, day) = latestDate.split('-')

    return redirect(url_for('do_report', year=year, month=month, day=day, format=format))
"""

@daily_report.route('/day/<int:year>/<int:month>/<int:day>/', defaults={'format': 'html'})
@daily_report.route('/day/<int:year>/<int:month>/<int:day>/report.<any(u"atom", u"html", u"json"):format>')
def do_daily_report(year, month, day, format):
    try:
        ts = datetime(year, month, day)
    except ValueError, e:
        abort(400)

    daily_report = g.mdb.daily_reports.find_one({'date': ts})
    if daily_report is None:
        abort(404)

    if format=='atom':
        response = make_response(render_template('feed.xml',
                                                 reports=process_report_atom(daily_report['reports'])))
        response.mimetype = "application/atom+xml"
    elif format=='html':
        response = make_response(render_template('report.html',
                                                 reports=daily_report['reports']))
    elif format=='json':
        response = make_response(json.dumps({'reports': daily_report['reports']},
                                            indent=None if request.is_xhr else 2,
                                            default=bson.json_util.default))
        response.mimetype = "application/json"

    #rv.last_modified = datetime.utcfromtimestamp(float(g.db.hget(key, "parse_ts")))
    response.add_etag()
    response.make_conditional(request)
    return response

@daily_report.route('/day/<int:year>/<int:month>/<int:day>/input.html')
def do_input(year, month, day):
    try:
        ts = datetime(year, month, day)
    except ValueError:
        abort(400)

    daily_report = g.mdb.daily_reports.find_one({'date': ts})

    input_file = g.fs.get(daily_report['input_id'])


    response = send_file(input_file, mimetype="text/html",
                         add_etags=False)

    response.add_etag()
    response.make_conditional(request)
    return response
