from datetime import datetime, timedelta
import uuid
from urllib2 import URLError

from flask import g

from cadorsfeed.cadorslib.fetch import fetch_daily_report, fetch_latest_date
from cadorsfeed.cadorslib.fetch import ReportNotFoundError, ReportFetchError
from cadorsfeed.cadorslib.parse import parse_daily_report


def latest_daily_report():
    latest = g.mdb.latest_daily_report.find_one({})
    if latest is None or (datetime.utcnow() - \
                              latest['fetch_time']) > timedelta(hours=12):
        latest = {'report_date': datetime.strptime(fetch_latest_date(),
                                                   "%Y-%m-%d"),
                  'fetch_time': datetime.utcnow()}
        g.mdb.latest_daily_report.save(latest)
    return latest['report_date']

def conditional_fetch(report_date, refetch=False):
    if not g.fs.exists(filename=report_date) or refetch:
        try:
            report_data = fetch_daily_report(report_date)
        except (URLError, ReportFetchError, ReportNotFoundError):
            raise
        g.fs.put(report_data, filename=report_date, encoding='utf-8',
                 date=report_date, fetch_date=datetime.utcnow())
        
    return g.fs.get_last_version(filename=report_date)

def retrieve_report(report_date):

    try:
        report_file = conditional_fetch(report_date.strftime("%Y-%m-%d"))
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
            g.mdb.locations.remove({'report.$id':stored_report['_id']})
            for location in stored_report['locations']:
                location['report'] = stored_report
                g.mdb.locations.save(location)

            daily_report['reports'].append(stored_report)
        
        stored_daily_report = g.mdb.daily_reports.find_one(
            {'date': daily_report['date']}) or {}
        stored_daily_report.update(daily_report)
        stored_daily_report['input_id'] = report_file._id
        g.mdb.daily_reports.save(stored_daily_report)
