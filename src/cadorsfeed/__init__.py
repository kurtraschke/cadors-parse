import os
from functools import partial

from flask import Flask, request, url_for
from flaskext.csrf import csrf
from flaskext.sqlalchemy import SQLAlchemy

etc = partial(os.path.join, 'parts', 'etc')
_buildout_path = __file__
for i in range(3 + __name__.count('.')):
    _buildout_path = os.path.dirname(_buildout_path)

abspath = partial(os.path.join, _buildout_path)
del _buildout_path


db = SQLAlchemy()

def create_app(config=None):
    app = Flask(__name__)
    if config is not None:
        app.config.from_pyfile(abspath(etc(config)))
    from cadorsfeed.views.daily_report import daily_report
    from cadorsfeed.views.report import report
    from cadorsfeed.views.search import search
    app.register_module(daily_report)
    app.register_module(report)
    app.register_module(search)
    app.add_url_rule('/favicon.ico', 'favicon', redirect_to='/static/favicon.ico')
    csrf(app)
    db.init_app(app)

    def modified_url_for(**updates):
        args = request.args.to_dict(flat=True)
        args.update(request.view_args)
        args.update(updates)
        return url_for(request.endpoint, **args)
    app.jinja_env.globals['modified_url_for'] = modified_url_for

    return app
