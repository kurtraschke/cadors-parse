from datetime import datetime, timedelta
import uuid
from urllib2 import URLError

from geoalchemy import WKTSpatialElement

from cadorsfeed.models import *
from cadorsfeed import db
from cadorsfeed.cadorslib.fetch import fetch_daily_report, fetch_latest_date
from cadorsfeed.cadorslib.fetch import ReportNotFoundError, ReportFetchError
from cadorsfeed.cadorslib.parse import parse_daily_report


def latest_daily_report():
    return datetime.strptime(fetch_latest_date(),
                             "%Y-%m-%d")

    """
    latest = g.mdb.latest_daily_report.find_one({})
    if latest is None or (datetime.utcnow() - \
                              latest['fetch_time']) > timedelta(hours=12):
        latest = {'report_date': datetime.strptime(fetch_latest_date(),
                                                   "%Y-%m-%d"),
                  'fetch_time': datetime.utcnow()}
        g.mdb.latest_daily_report.save(latest)
    return latest['report_date']
    """


def conditional_fetch(report_date, refetch=False):
    daily_report = DailyReport.query.filter(
        DailyReport.report_date == report_date).first()

    if daily_report is None:
        daily_report = DailyReport(report_date=report_date)
        db.session.add(daily_report)
    if daily_report.report_html is None or refetch:
        try:
            daily_report.report_html = fetch_daily_report(
                report_date.strftime("%Y-%m-%d")).encode('utf-8')
            daily_report.fetch_timestamp = datetime.utcnow()
        except (URLError, ReportFetchError, ReportNotFoundError):
            raise
        db.session.commit()

    return daily_report.report_html


def retrieve_report(report_date):
    try:
        report_file = conditional_fetch(report_date)
    except (URLError, ReportFetchError, ReportNotFoundError):
        raise

    parsed_daily_report = parse_daily_report(report_file)

    #We might be updating a report which already exists.
    daily_report = DailyReport.query.filter(
        DailyReport.report_date == report_date).first()

    daily_report.parse_timestamp = datetime.utcnow()

    reports = []

    for parsed_report in parsed_daily_report['reports']:

        categories = []
        for category in parsed_report['categories']:
            categories.append(ReportCategory(text=category))
        del parsed_report['categories']

        aircraft_parts = []
        for aircraft_part in parsed_report['aircraft']:
            aircraft_parts.append(Aircraft(**aircraft_part))
        del parsed_report['aircraft']

        narrative_parts = []
        for narrative_part in parsed_report['narrative']:
            narrative_parts.append(NarrativePart(**narrative_part))
        del parsed_report['narrative']

        locations = []
        for location in parsed_report['locations']:
            wkt = "POINT(%s %s)" % (location['longitude'],
                                    location['latitude'])
            location['location'] = WKTSpatialElement(wkt)
            del location['latitude']
            del location['longitude']
            locations.append(Location(**location))
        del parsed_report['locations']

        report = CadorsReport.query.get(
            parsed_report['cadors_number']) or CadorsReport(uuid=uuid.uuid4())

        for key, value in parsed_report.iteritems():
            setattr(report, key, value)

        report.categories = categories
        report.aircraft = aircraft_parts
        report.narrative_parts = narrative_parts
        report.locations = locations

        reports.append(report)

    daily_report.reports = reports
    db.session.commit()
