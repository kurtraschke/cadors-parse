from urllib2 import URLError
from datetime import datetime
import time

from flask import abort, request, redirect, url_for, g, make_response, session, flash, render_template, Module
from flask import current_app as app
from pyrfc3339 import generate

from cadorsfeed.cadorslib.fetch import ReportNotFoundError, ReportFetchError


feeds = Module(__name__)


@feeds.route("/report/<report>")
def fetch_report(report):
    report = g.mdb.reports.find_one({'cadors_number': report})
    report['authors'] = set([narrative['name'] for narrative in report['narrative']])
    response = make_response(render_template('feed.xml', reports=[report]))
    response.mimetype = "application/atom+xml"
    return response



@feeds.route("/report/<report>/kml")
def fetch_report_kml(report):
    report = g.mdb.reports.find_one({'cadors_number': report})
    locations = g.mdb.locations.find({'report.$id': report['_id']})

    response = make_response(render_template('kml.xml', locations=locations))
    response.mimetype = "application/vnd.google-earth.kml+xml"
    return response


@feeds.route("/reports")
def fetch_reports():
    reports = g.mdb.reports.find()
    out = []
    for report in reports:
        report['authors'] = set([narrative['name'] for narrative in report['narrative']])
        report['atom_ts'] = ''
        out.append(report)
    response = make_response(render_template('feed.xml', reports=out))
    response.mimetype = "application/atom+xml"
    return response

#@feeds.route("/test")
#def test():
#    from cadorsfeed.filters.aerodromes import aerodromes_re
#    return aerodromes_re.get_icao_re.pattern


def process_reports():
    out = []
    for report in reports:
        report['authors'] = set([narrative['name'] for narrative in report['narrative']])
        report['atom_ts'] = generate(report['timestamp'])
        out.append(report)
    return out
        


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

@feeds.route('/day/<int:year>/<int:month>/<int:day>/', defaults={'format': 'atom'})
@feeds.route('/day/<int:year>/<int:month>/<int:day>/<any(u"atom", u"html"):format>')
def do_report(year, month, day, format):
    try:
        ts = datetime(year, month, day)
    except ValueError, e:
        abort(400)

    daily_report = g.mdb.daily_reports.find_one({'date': ts})

    out = []
    for report in daily_report['reports']:
        report['authors'] = set([narrative['name'] for narrative in report['narrative']])
        report['atom_ts'] = ''
        out.append(report)

    response = make_response(render_template('feed.xml', reports=out))
    response.mimetype = "application/atom+xml"
    #rv.last_modified = datetime.utcfromtimestamp(float(g.db.hget(key, "parse_ts")))
    #rv.add_etag()
    #rv.make_conditional(request)
    return response

@feeds.route('/day/<int:year>/<int:month>/<int:day>/input')
def do_input(year, month, day):
    try:
        ts = datetime(year, month, day)
    except ValueError:
        abort(400)

    daily_report = g.mdb.daily_reports.find_one({'date': ts})
    
    input_file = g.fs.get(daily_report['input_id'])

    
    rv = app.make_response(input_file.read())
    rv.mimetype = "text/html"
    #rv.last_modified = datetime.utcfromtimestamp(float(g.db.hget(key, "fetch_ts")))
    #rv.add_etag()
    #rv.make_conditional(request)
    return rv
