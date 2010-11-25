import redis
from datetime import date

from flask import request, redirect, url_for, g, session, Module, render_template, flash
from werkzeug.exceptions import NotFound
from flask import current_app as app

from cadorsfeed.views.pagination import Pagination

frontend = Module(__name__)


@frontend.route('/reports/', defaults={'page': 1})
@frontend.route('/reports/<int:page>')
def list(page):
    pagination = Pagination(g.db, 'reports', 20, page, 'list')
    if pagination.page > 1 and not pagination.entries:
        raise NotFound()

    reports = []
    for key in pagination.entries:
        date, hits = g.db.hmget(key, ['date', 'hits'])
        (year, month, day) = date.split('-')

        reports.append({'date': date,
                        'hits': hits or 0,
                        'html_link': url_for('feeds.do_report', year=year, month=month, day=day,
                                             format='html'),
                        'atom_link': url_for('feeds.do_report', year=year, month=month, day=day,
                                             format='atom'),
                        'input_link': url_for('feeds.do_input', year=year, month=month, day=day),
                        'clear_link': url_for('frontend.do_clear_cache', year=year, month=month, day=day)})
    return render_template('list.html', reports=reports, pagination=pagination)


@frontend.route('/report/<int:year>/<int:month>/<int:day>/clear', methods=['POST'])
def do_clear_cache(year, month, day):
    if not session.get('logged_in', False):
        flash('You must be logged in to clear report caches.')
        return redirect(url_for('auth.login_form'))

    try:
        ts = date(int(year), int(month), int(day))
    except ValueError, e:
        abort(400)

    input = (request.form['submit'] == "input")

    key = "report:" + ts.isoformat()

    g.db.hdel(key, 'output')
    g.db.hdel(key, 'output_html')
    flash("Output cache deleted for report %s." % ts.isoformat())
    if input:
        g.db.hdel(key, 'input')
        flash("Input cache deleted for report %s." % ts.isoformat())

    return redirect(request.referrer)


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.before_request
def before_request():
    g.db = redis.Redis(host=app.config['REDIS_HOST'],
                       port=app.config['REDIS_PORT'],
                       db=app.config['REDIS_DB'])
