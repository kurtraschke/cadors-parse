from datetime import datetime
import json

from flask import abort, request, redirect, url_for
from flask import make_response, render_template, Module
from pyrfc3339 import generate
from sqlalchemy import func, select

from cadorsfeed import db
from cadorsfeed.models import DailyReport, CadorsReport, report_map
from cadorsfeed.views.util import process_report_atom, json_default

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

    return render_template('daily_report_list.html',
                           daily_reports=pagination.items,
                           pagination=pagination)


@daily_report.route('/daily-report/latest/', defaults={'format': 'html'})
@daily_report.route('/daily-report/latest/' \
                        'report.<any(u"atom", u"html", u"json"):format>')
def latest_report(format):
    report = DailyReport.query.order_by(
        DailyReport.report_date.desc()).first()

    (year, month, day) = report.report_date.utctimetuple()[0:3]

    return redirect(url_for('do_daily_report', year=year, month=month,
                            day=day, format=format))


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

    if format == 'atom':
        reports = process_report_atom(daily_report.reports)
        feed_timestamp = generate(daily_report.last_updated, accept_naive=True)
        response = make_response(render_template('feed.xml',
                                                 feed_timestamp=feed_timestamp,
                                                 reports=reports))
        response.mimetype = "application/atom+xml"
    elif format == 'html':
        next_report = DailyReport.query.filter(
            DailyReport.report_date > ts).order_by(
            DailyReport.report_date.asc()).first()

        previous_report = DailyReport.query.filter(
            DailyReport.report_date < ts).order_by(
            DailyReport.report_date.desc()).first()

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
                            previous_report=previous_report,
                            next_report=next_report,
                            first=DailyReport.first(),
                            last=DailyReport.last()))
    elif format == 'json':
        response = make_response(json.dumps(
                {'reports': daily_report.reports},
                indent=None if request.is_xhr else 2,
                default=json_default))
        response.mimetype = "application/json"

    response.add_etag()
    response.make_conditional(request)
    return response


@daily_report.route('/daily-report/<int:year>/<int:month>/<int:day>/' \
                        'input.html')
def do_input(year, month, day):
    try:
        ts = datetime(year, month, day)
    except ValueError:
        abort(400)

    daily_report = DailyReport.query.filter(
        DailyReport.report_date == ts).first_or_404()

    response = make_response(unicode(daily_report.report_html,
                                     'utf-8'))
    response.mimetype = 'text/html'
    response.add_etag()
    response.make_conditional(request)
    return response
