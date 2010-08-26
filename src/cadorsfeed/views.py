from werkzeug import redirect, Response
from werkzeug.exceptions import NotFound, ServiceUnavailable, InternalServerError, BadRequest
from urllib2 import URLError
from datetime import date
import time

from cadorsfeed.utils import expose, url_for, db
from cadorsfeed.parse import parse
from cadorsfeed.fetch import fetchLatest, fetchReport


@expose('/report/latest/', defaults={'format': 'atom'})
@expose('/report/latest/<any(u"atom", u"html"):format>')
def latest_report(request, format):
    if 'latest' in db:
        latestDate = db['latest']
    else:
        latestDate = fetchLatest()
        db.setex('latest', latestDate, 60 * 60 * 12)

    (year, month, day) = latestDate.split('-')

    return redirect(url_for('do_report', year=year, month=month, day=day, format=format))


@expose('/report/<int:year>/<int:month>/<int:day>/', defaults={'format': 'atom'})
@expose('/report/<int:year>/<int:month>/<int:day>/<any(u"atom", u"html"):format>')
def do_report(request, year, month, day, format):
    refetch = request.args.get('refetch', '0') == '1'
    reparse = request.args.get('reparse', '0') == '1' or refetch

    try:
        ts = date(year, month, day)
    except ValueError, e:
        raise BadRequest(e)
    
    key = "report:" + ts.isoformat()

    process_report(key, ts, refetch, reparse)

    db.hincrby(key, "hits")

    if format == "atom":
        output = db.hget(key, "output")
        mimetype = "application/atom+xml"
    elif format == "html":
        output = db.hget(key, "output_html")
        mimetype = "text/html"

    resp = Response(output.decode("utf-8"), mimetype=mimetype)
    resp.add_etag()
    return resp.make_conditional(request)


@expose('/report/<int:year>/<int:month>/<int:day>/input')
def do_input(request, year, month, day):
    try:
        ts = date(year, month, day)
    except ValueError:
        raise BadRequest(e)
    
    key = "report:" + ts.isoformat()

    if db.hexists(key, "input"):
        resp = Response(db.hget(key, "input").decode('utf-8'),
                        mimetype="text/html")
        resp.add_etag()
        return resp.make_conditional(request)
    else:
        return NotFound()


def process_report(key, report_date, refetch=False, reparse=False):
    if (not db.hexists(key, "output")) or (not db.hexists(key, "output_html")) or reparse:
        if db.hexists(key, "input") and not refetch:
            input = db.hget(key, "input").decode('utf-8')
        else:
            lock = db.lock("fetch:" + key, timeout=120)
            if lock.acquire(blocking=False):
                try:
                    input = fetchReport(report_date.isoformat())
                    db.hset(key, "input", input)
                    db.hset(key, "date", report_date.isoformat())
                    db.hset(key, "fetch_ts", time.time())
                    db.zadd("reports", key, report_date.toordinal())
                except URLError, e:
                    raise InternalServerError(e)
                except NotFound, e:
                    raise e
                except InternalServerError, e:
                    raise e
                finally:
                    lock.release()
            else:
                raise ServiceUnavailable()

        lock = db.lock("parse:" + key, timeout=120)
        if lock.acquire(blocking=False):
            try:
                db.hmset(key, parse(input))
                db.hset(key, "parse_ts", time.time())
            except Exception, e:
                raise InternalServerError(e)
            finally:
                lock.release()
        else:
            raise ServiceUnavailable()
