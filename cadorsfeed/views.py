from werkzeug import redirect, Response
from werkzeug.exceptions import NotFound
from cadorsfeed.utils import expose, url_for, db
from parse import parse
from fetch import fetchLatest, fetchReport

@expose('/report/latest/')
def latest_report(request):

    if 'latest' in db:
        latestDate = db['latest']
    else:
        latestDate = fetchLatest()

        db['latest'] = latestDate
        db.expire('latest',60*60)
    
    (year, month, day) = latestDate.split('-')
    
    return redirect(url_for('do_report', year=year, month=month, day=day))

@expose('/report/<int:year>/<int:month>/<int:day>/')
def do_report(request, year, month, day):
    refetch = request.args.get('refetch','0') == '1'
    reparse = request.args.get('reparse','0') == '1' or refetch
    
    date = "{year:04.0f}-{month:02.0f}-{day:02.0f}".format(
        year=year, month=month, day=day)

    key = "report:"+date

    if db.hexists(key, "output") and not reparse:
        output = db.hget(key, "output")
    else:
        if db.hexists(key, "input") and not refetch:
            input = db.hget(key, "input").decode('utf-8')
        else:
            input = fetchReport(date)
            db.hset(key, "input", input)
            
        output = parse(input)
        db.hset(key,"output", output)

    return Response(output, mimetype="application/atom+xml")
