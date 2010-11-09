import redis

from flask import request, redirect, url_for, g, session, Module, render_template, flash
from flask import current_app as app

from werkzeug.exceptions import Unauthorized
from werkzeug import Response
from cadorsfeed.auth import verify

auth = Module(__name__)

@auth.route('/login', methods=['GET', 'POST'])
@auth.route('/login/form', methods=['GET', 'POST'])
def login_form():
    if request.method == 'POST':
        if verify(request.form['username'], request.form['password']):
            session['logged_in'] = True
            session['username'] = request.form['username']
            return redirect('index.index')
        else:
            flash("Invalid username or password")
            return render_template('login.html')
    else:
        return render_template('login.html')

@auth.route('/logout')
def logout():
    del session['logged_in']
    del session['username']
    return redirect('index.index')

@auth.before_request
def before_request():
    g.db = redis.Redis(host=app.config['REDIS_HOST'],
                       port=app.config['REDIS_PORT'],
                       db=app.config['REDIS_DB'])
