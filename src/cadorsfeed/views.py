from urllib2 import URLError
from datetime import date
from flask import abort, request, redirect, url_for, g, make_response
import redis
import time

from cadorsfeed import app
from cadorsfeed.parse import parse
from cadorsfeed.fetch import fetchLatest, fetchReport, ReportNotFoundError, ReportFetchError


@app.route('/report/latest/', defaults = {'format': 'atom'})
@app.route('/report/latest/<any(u"atom", u"html"):format>')
def latest_report(format):
    if 'latest' in g.db:
        latestDate = g.db['latest']
    else:
        try:
            latestDate = fetchLatest()
            g.db.setex('latest', latestDate, 60 * 60 * 12)
        except Exception, e:
            abort(500)

    (year, month, day) = latestDate.split('-')

    return redirect(url_for('do_report', year=year, month=month, day=day, format=format))


@app.route('/report/<int:year>/<int:month>/<int:day>/', 
           defaults={'format': 'atom'})
@app.route('/report/<int:year>/<int:month>/<int:day>/<any(u"atom", u"html"):format>')
def do_report(year, month, day, format):
    refetch = request.args.get('refetch', '0') == '1'
    reparse = request.args.get('reparse', '0') == '1' or refetch

    try:
        ts = date(year, month, day)
    except ValueError, e:
        abort(400)
    
    key = "report:" + ts.isoformat()

    process_report(key, ts, refetch, reparse)

    g.db.hincrby(key, "hits")

    if format == "atom":
        output = g.db.hget(key, "output")
        mimetype = "application/atom+xml"
    elif format == "html":
        output = g.db.hget(key, "output_html")
        mimetype = "text/html"

    rv = app.make_response(output.decode("utf-8"))
    rv.mimetype = mimetype
    return rv


@app.route('/report/<int:year>/<int:month>/<int:day>/input')
def do_input(year, month, day):
    try:
        ts = date(year, month, day)
    except ValueError:
        abort(400)
    
    key = "report:" + ts.isoformat()

    if g.db.hexists(key, "input"):
        rv = app.make_response(g.db.hget(key, "input").decode('utf-8'))
        rv.mimetype = "text/html"
        return rv
    else:
        abort(404)

def process_report(key, report_date, refetch=False, reparse=False):
    if (not g.db.hexists(key, "output")) or (not g.db.hexists(key, "output_html")) or reparse:
        if g.db.hexists(key, "input") and not refetch:
            input = g.db.hget(key, "input").decode('utf-8')
        else:
            lock = g.db.lock("fetch:" + key, timeout=120)
            if lock.acquire(blocking=False):
                try:
                    input = fetchReport(report_date.isoformat())
                    g.db.hset(key, "input", input)
                    g.db.hset(key, "date", report_date.isoformat())
                    g.db.hset(key, "fetch_ts", time.time())
                    g.db.zadd("reports", key, report_date.toordinal())
                except (URLError, ReportFetchError), e:
                    raise
                except ReportNotFoundError, e:
                    abort(404)
                finally:
                    lock.release()
            else:
                abort(503)
        lock = g.db.lock("parse:" + key, timeout=120)
        if lock.acquire(blocking=False):
            try:
                g.db.hmset(key, parse(input))
            except Exception, e:
                raise
            finally:
                lock.release()
        else:
            abort(503)

@app.before_request
def before_request():
    g.db = redis.Redis(host=app.config['REDIS_HOST'],
                       port=app.config['REDIS_PORT'],
                       db=app.config['REDIS_DB'])
