from werkzeug import redirect, Response
from werkzeug.exceptions import NotFound, ServiceUnavailable, InternalServerError
from urllib2 import URLError

from cadorsfeed.utils import expose, url_for, db
from cadorsfeed.parse import parse, generate_html
from cadorsfeed.fetch import fetchLatest, fetchReport


@expose('/report/latest/')
def latest_report(request):

    if 'latest' in db:
        latestDate = db['latest']
    else:
        latestDate = fetchLatest()
        db.setex('latest', latestDate, 60 * 60 * 12)

    (year, month, day) = latestDate.split('-')

    return redirect(url_for('do_report', year=year, month=month, day=day))


@expose('/report/<int:year>/<int:month>/<int:day>/')
def do_report(request, year, month, day):
    refetch = request.args.get('refetch', '0') == '1'
    reparse = request.args.get('reparse', '0') == '1' or refetch

    date = "{year:04.0f}-{month:02.0f}-{day:02.0f}".format(
        year=year, month=month, day=day)

    key = "report:" + date

    if db.hexists(key, "output") and not reparse:
        output = db.hget(key, "output").decode('utf-8')
    else:
        if db.hexists(key, "input") and not refetch:
            input = db.hget(key, "input").decode('utf-8')
        else:
            lock = db.lock("fetch:" + key, timeout=120)
            if lock.acquire(blocking=False):
                try:
                    input = fetchReport(date)
                    db.hset(key, "input", input)
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
                output = parse(input)
                db.hset(key, "output", output)
            except Exception, e:
                raise InternalServerError(e)
            finally:
                lock.release()
        else:
            raise ServiceUnavailable()
    db.hincrby(key, "hits")

    resp = Response(output, mimetype="application/xml")
    resp.add_etag()
    return resp.make_conditional(request)


@expose('/report/<int:year>/<int:month>/<int:day>/input')
def do_input(request, year, month, day):
    date = "{year:04.0f}-{month:02.0f}-{day:02.0f}".format(
        year=year, month=month, day=day)

    key = "report:" + date

    if db.hexists(key, "input"):
        resp = Response(db.hget(key, "input"), mimetype="text/html")
        resp.add_etag()
        return resp.make_conditional(request)
    else:
        return NotFound()

@expose('/report/<int:year>/<int:month>/<int:day>/html')
def do_html(request, year, month, day):
    date = "{year:04.0f}-{month:02.0f}-{day:02.0f}".format(
        year=year, month=month, day=day)

    key = "report:" + date

    if db.hexists(key, "output"):
        
        resp = Response(generate_html(db.hget(key,"output").decode('utf-8')), 
                        mimetype="text/html")
        resp.add_etag()
        return resp.make_conditional(request)
    else:
        return NotFound()
