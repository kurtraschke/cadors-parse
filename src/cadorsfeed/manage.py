from flaskext.script import Manager, prompt_pass, prompt_bool
from flask import g
from functools import wraps

from cadorsfeed import create_app
from cadorsfeed.db import setup_db

manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config', required=False)


def with_db(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        setup_db()
        return f(*args, **kwargs)
    return wrapper

@manager.option('-d', '--date', dest='report_date', required=True)
@with_db
def retrieve(report_date):
    from datetime import datetime
    from cadorsfeed.retrieve import retrieve_report
    retrieve_report(datetime.strptime(report_date, "%Y-%m-%d"))

@manager.command
@with_db
def retrieve_today():
    from cadorsfeed.retrieve import retrieve_report, latest_daily_report
    report_date = latest_daily_report()
    retrieve_report(report_date)
    print "Retrieved daily report for %s." % report_date

@manager.command
@with_db
def load_aerodromes():
    '''Load or update aerodrome data from DBpedia'''
    from cadorsfeed.cadorslib.filters.aerodromes import fetch_aerodromes
    fetch_aerodromes()

@manager.command
@with_db
def load_iata_blacklist():
    '''Load or update blacklist of IATA codes which produce false positives'''
    from cadorsfeed.cadorslib.filters.aerodromes import import_blacklist
    import_blacklist()


def run():
    manager.run()
