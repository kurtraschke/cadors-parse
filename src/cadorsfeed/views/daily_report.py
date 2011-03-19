from datetime import datetime
from collections import defaultdict
import json

from flask import abort, request, redirect, url_for, g
from flask import make_response, render_template, send_file, Module
from flask import current_app as app
import bson.json_util
import pymongo

from cadorsfeed.views.util import process_report_atom
from cadorsfeed.retrieve import latest_daily_report 

daily_report = Module(__name__)

@daily_report.route('/day/latest/', defaults={'format': 'html'})
@daily_report.route('/day/latest/report.<any(u"atom", u"html", u"json"):format>')
def latest_report(format):
    report = g.mdb.daily_reports.find_one({},
                                 sort=[('date',
                                        pymongo.DESCENDING)],
                                 fields=['date'])

    (year, month, day) = report['date'].utctimetuple()[0:3]

    return redirect(url_for('do_daily_report', year=year, month=month,
                            day=day, format=format))


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
        next_report = g.mdb.daily_reports.find_one({'date': {'$gt': ts}},
                                                    sort=[('date',
                                                           pymongo.ASCENDING)],
                                                   fields=['date'])
        previous_report = g.mdb.daily_reports.find_one({'date': {'$lt': ts}},
                                                        sort=[('date',
                                                               pymongo.DESCENDING)],
                                                       fields=['date'])

        types = defaultdict(int)
        regions = defaultdict(int)
        
        daily_report['reports'].sort(key=lambda r: r['timestamp'], reverse=True)

        for report in daily_report['reports']:
            types[report['type']] += 1
            regions[report['region']] += 1
        
            response = make_response(render_template('daily_report.html',
                                                     reports=daily_report['reports'],
                                                     types=types,
                                                     regions=regions,
                                                     previous_report=previous_report,
                                                     next_report=next_report
                                                     ))
    elif format=='json':
        response = make_response(json.dumps({'reports': daily_report['reports']},
                                            indent=None if request.is_xhr else 2,
                                            default=bson.json_util.default))
        response.mimetype = "application/json"

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
