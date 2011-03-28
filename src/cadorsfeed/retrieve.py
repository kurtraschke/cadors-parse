import uuid
from datetime import datetime
from urllib2 import URLError

from geoalchemy import WKTSpatialElement

from cadorsfeed import db
from cadorsfeed.models import DailyReport, CadorsReport, ReportCategory
from cadorsfeed.models import Aircraft, NarrativePart, Location
from cadorsfeed.cadorslib.fetch import fetch_daily_report, fetch_latest_date
from cadorsfeed.cadorslib.fetch import ReportNotFoundError, ReportFetchError
from cadorsfeed.cadorslib.parse import parse_daily_report
from cadorsfeed.fpr import format_parsed_report

def latest_daily_report():
    return datetime.strptime(fetch_latest_date(), "%Y-%m-%d")


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
        report = format_parsed_report(parsed_report)
        reports.append(report)        

    daily_report.reports = reports
    db.session.commit()
