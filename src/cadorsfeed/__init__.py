import os

from flask import Flask, request, url_for
from flaskext.sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix


db = SQLAlchemy()

def modified_url_for(**updates):
    args = request.args.to_dict(flat=True)
    args.update(request.view_args)
    args.update(updates)
    return url_for(request.endpoint, **args)

def create_app(config):
    app = Flask(__name__)
    app.config.from_pyfile(os.path.abspath(config))
    from cadorsfeed.views.daily_report import daily_report
    from cadorsfeed.views.report import report
    from cadorsfeed.views.category import category
    from cadorsfeed.views.search import search
    from cadorsfeed.views.about import about
    app.register_module(daily_report)
    app.register_module(report)
    app.register_module(category)
    app.register_module(search)
    app.register_module(about)
    app.add_url_rule('/favicon.ico', 'favicon',
                     redirect_to='/static/favicon.ico')
    db.init_app(app)

    app.jinja_env.globals['modified_url_for'] = modified_url_for
    app.jinja_env.globals['config'] = app.config
    
    if app.config['PROXY_FIX']:
        app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
