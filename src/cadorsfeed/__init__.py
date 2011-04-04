import os
from functools import partial

from flask import Flask, request, url_for
from flaskext.sqlalchemy import SQLAlchemy

etc = partial(os.path.join, 'parts', 'etc')
_buildout_path = __file__
for i in range(3 + __name__.count('.')):
    _buildout_path = os.path.dirname(_buildout_path)

abspath = partial(os.path.join, _buildout_path)
del _buildout_path

db = SQLAlchemy()

def modified_url_for(**updates):
    args = request.args.to_dict(flat=True)
    args.update(request.view_args)
    args.update(updates)
    return url_for(request.endpoint, **args)

def create_app(config=None):
    app = Flask(__name__)
    if config is not None:
        app.config.from_pyfile(abspath(etc(config)))
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

    return app
