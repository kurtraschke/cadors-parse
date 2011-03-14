import datetime
import uuid
from urllib2 import URLError

from flask import g

from cadorsfeed.cadorslib.fetch import fetch_daily_report, ReportNotFoundError, ReportFetchError
from cadorsfeed.cadorslib.parse import parse_daily_report

def conditional_fetch(date):
    if not g.fs.exists(filename=date):
        try:
            report_data = fetch_daily_report(date)
        except (URLError, ReportFetchError, ReportNotFoundError):
            raise
        g.fs.put(report_data, filename=date, encoding='utf-8',
                 date=date, fetch_date=datetime.datetime.utcnow())
        
    return g.fs.get_last_version(filename=date)

def retrieve_report(date):
    ts =  datetime.datetime.strptime(date,
                                     "%Y-%m-%d")

    if g.mdb.daily_reports.find({'date': ts}).count() == 0:
        #Report does not exist, attempt to fetch
        try:
            report_file = conditional_fetch(date)
        except (URLError, ReportFetchError, ReportNotFoundError):
            raise

        (daily_report, reports) = parse_daily_report(report_file)
        
        for report in reports:
            stored_report = g.mdb.reports.find_one(
                {'cadors_number': report['cadors_number']}) or {}
            stored_report.update(report)
            if 'uuid' not in stored_report:
                stored_report['uuid'] = uuid.uuid4()
            g.mdb.reports.save(stored_report)
            daily_report['reports'].append(stored_report)
        
        stored_daily_report = g.mdb.daily_reports.find_one(
            {'date': daily_report['date']}) or {}
        stored_daily_report.update(daily_report)
        stored_daily_report['input_id'] = report_file._id
        g.mdb.daily_reports.save(stored_daily_report)
