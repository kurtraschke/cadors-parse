from flaskext.script import Manager, prompt_pass, prompt_bool
from functools import wraps

from cadorsfeed import create_app


manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config', required=False)


@manager.option('-d', '--date', dest='report_date', required=True)
def retrieve(report_date):
    from datetime import datetime
    from cadorsfeed.retrieve import retrieve_report
    retrieve_report(datetime.strptime(report_date, "%Y-%m-%d"))

@manager.command
def retrieve_today():
    from cadorsfeed.retrieve import retrieve_report, latest_daily_report
    report_date = latest_daily_report()
    retrieve_report(report_date)
    print "Retrieved daily report for %s." % report_date

@manager.command
def load_aerodromes():
    '''Load or update aerodrome data from DBpedia'''
    from cadorsfeed.aerodb import fetch_aerodromes
    fetch_aerodromes()

@manager.option('-a', '--aerodrome', dest='aerodrome', required=True)
def lookup(aerodrome):
    from cadorsfeed.aerodb import lookup
    from pprint import pprint
    pprint(dict(lookup(aerodrome)))

@manager.command
def load_iata_blacklist():
    '''Load or update blacklist of IATA codes which produce false positives'''
    from cadorsfeed.aerodb import import_blacklist
    import_blacklist()

@manager.command
def create_all():
    '''Create PostgreSQL tables'''
    from cadorsfeed import db
    from cadorsfeed.models import DailyReport, CadorsReport, ReportCategory
    from cadorsfeed.models import Aircraft, NarrativePart, Location
    from cadorsfeed.models import Aerodrome
    db.create_all()

@manager.command
def drop_all():
    '''Drop PostgreSQL tables'''
    from cadorsfeed import db
    from cadorsfeed.models import DailyReport, CadorsReport, ReportCategory
    from cadorsfeed.models import Aircraft, NarrativePart, Location
    from cadorsfeed.models import Aerodrome
    if prompt_bool("Are you sure you want to drop the database tables?"):
        db.drop_all()


def run():
    manager.run()
