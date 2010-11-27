from flaskext.script import Manager, prompt_pass, prompt_bool
from flask import g
from functools import wraps
import redis

from cadorsfeed import create_app
from cadorsfeed.auth import set_password

manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config', required=False)


def with_db(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import g, current_app as app
        g.db = redis.Redis(host=app.config['REDIS_HOST'],
                        port=app.config['REDIS_PORT'],
                        db=app.config['REDIS_DB'])
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


@manager.command
@with_db
def load_aerodromes():
    '''Load or update aerodrome data from DBpedia'''
    from cadorsfeed.filters.aerodromes import fetch_aerodromes
    fetch_aerodromes()


def run():
    manager.run()
