from datetime import datetime
import json

from flask import abort, request, redirect, url_for
from flask import make_response, render_template, Module
from pyrfc3339 import generate
from sqlalchemy import func, select

from cadorsfeed import db
from cadorsfeed.models import DailyReport, CadorsReport, report_map
from cadorsfeed.views.util import process_report_atom, json_default, prepare_response

daily_report = Module(__name__)

@daily_report.route('/daily-reports/', defaults={'page': 1})
@daily_report.route('/daily-reports/<int:page>')
def daily_reports_list(page):
    query = DailyReport.query
    query = query.add_column(
        select(
            [func.count()],
            report_map.c.daily_report_id == \
                DailyReport.daily_report_id).select_from(
                    report_map).label('report_count'))
    

    pagination = query.paginate(page)

    response = make_response(render_template('daily_report_list.html',
                           daily_reports=pagination.items,
                           pagination=pagination))
    
    return prepare_response(response, 3600)


@daily_report.route('/daily-report/latest/', defaults={'format': 'html'})
@daily_report.route('/daily-report/latest/' \
                        'report.<any(u"atom", u"html", u"json"):format>')
def latest_report(format):
    report = DailyReport.query.order_by(
        DailyReport.report_date.desc()).first()

    (year, month, day) = report.report_date.utctimetuple()[0:3]

    return redirect(url_for('do_daily_report', year=year, month=month,
                            day=day, format=format))

@daily_report.route('/daily-report/')
def daily_report_redirect():
    (year, month, day) = request.args['report_date'].split('-')

    return redirect(url_for('do_daily_report', year=year, month=month,
                            day=day))

@daily_report.route('/daily-report/<int:year>/<int:month>/<int:day>/',
                    defaults={'format': 'html'})
@daily_report.route('/daily-report/<int:year>/<int:month>/<int:day>/' \
                        'report.<any(u"atom", u"html", u"json"):format>')
def do_daily_report(year, month, day, format):
    try:
        ts = datetime(year, month, day)
    except ValueError:
        abort(400)

    daily_report = DailyReport.query.filter(
        DailyReport.report_date == ts).first_or_404()

    first = DailyReport.first()
    last = DailyReport.last()
        
    prev = DailyReport.query.filter(
        DailyReport.report_date < ts).order_by(
        DailyReport.report_date.desc()).first()
        
    next = DailyReport.query.filter(
        DailyReport.report_date > ts).order_by(
        DailyReport.report_date.asc()).first()

    if format == 'atom':
        reports = process_report_atom(daily_report.reports)
        feed_timestamp = generate(daily_report.last_updated, accept_naive=True)
        title = "Daily Report for %s" % ts.strftime("%Y-%m-%d")
        response = make_response(
            render_template('feed.xml',
                            feed_timestamp=feed_timestamp,
                            reports=reports,
                            title=title,
                            first=first.link(format='atom', _external=True),
                            prev=prev.link(format='atom', _external=True) \
                                if prev is not None else None,
                            next=next.link(format='atom', _external=True) \
                                if next is not None else None,
                            last=last.link(format='atom', _external=True)))
        response.mimetype = "application/atom+xml"
    elif format == 'html':
        occurrence_type = CadorsReport.occurrence_type
        type_count = func.count(CadorsReport.region)

        types = db.session.query(occurrence_type, type_count).group_by(
            occurrence_type).with_parent(
            daily_report).order_by(type_count.desc()).all()

        region = CadorsReport.region
        region_count = func.count(CadorsReport.region)

        regions = db.session.query(region, region_count).group_by(
            region).with_parent(
            daily_report).order_by(region_count.desc()).all()

        response = make_response(
            render_template('daily_report.html',
                            daily_report=daily_report,
                            reports=daily_report.reports,
                            types=types,
                            regions=regions,
                            prev=prev,
                            next=next,
                            first=first,
                            last=last))
    elif format == 'json':
        response = make_response(json.dumps(
                {'reports': daily_report.reports},
                indent=None if request.is_xhr else 2,
                default=json_default))
        response.mimetype = "application/json"

    response.last_modified = daily_report.last_updated
    return prepare_response(response, 43200)


@daily_report.route('/daily-report/<int:year>/<int:month>/<int:day>/' \
                        'input.html')
def do_input(year, month, day):
    try:
        ts = datetime(year, month, day)
    except ValueError:
        abort(400)

    daily_report = DailyReport.query.filter(
        DailyReport.report_date == ts).first_or_404()

    filename = "report-%04d%02d%02d.html" % (year, month, day)

    response = make_response(unicode(daily_report.report_html,
                                     'utf-8'))
    response.mimetype = 'text/html'
    response.headers['Content-disposition'] = "attachment; filename=%s" % (filename)
    return prepare_response(response, 43200)
