from flaskext.script import Manager, prompt_pass, prompt_bool
from flask import g
from functools import wraps

from cadorsfeed import create_app
from cadorsfeed.auth import set_password
from cadorsfeed.db import setup_db

manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config', required=False)


def with_db(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        setup_db()
        return f(*args, **kwargs)
    return wrapper


@manager.option('-u', '--username', dest='username', required=True)
@with_db
def adduser(username):
    '''Add an administrative user'''
    password = prompt_pass("Enter password for user %s" % username)
    set_password(username, password)


@manager.option('-u', '--username', dest='username', required=True)
@with_db
def deluser(username):
    '''Add an administrative user'''
    if g.db.exists("users:" + username):
        confirm = prompt_bool("Are you sure you wish to delete user %s" % username)
        if confirm:
            g.db.delete("users:" + username)
    else:
        print "User %s does not exist." % username

@manager.option('-d', '--date', dest='date', required=True)
@with_db
def retrieve(date):
    from cadorsfeed.retrieve import retrieve_report
    retrieve_report(date)

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
