import os
from functools import partial

from pymongo import Connection

from flask import Flask, g
from flaskext.csrf import csrf

etc = partial(os.path.join, 'parts', 'etc')
_buildout_path = __file__
for i in range(3 + __name__.count('.')):
    _buildout_path = os.path.dirname(_buildout_path)

abspath = partial(os.path.join, _buildout_path)
del _buildout_path


def create_app(config=None):
    app = Flask(__name__)
    if config is not None:
        app.config.from_pyfile(abspath(etc(config)))
    from cadorsfeed.views.feeds import feeds
    from cadorsfeed.views.frontend import frontend
    from cadorsfeed.views.auth import auth
    app.register_module(feeds)
    app.register_module(frontend)
    app.register_module(auth)
    app.add_url_rule('/favicon.ico', 'favicon', redirect_to='/static/favicon.ico')
    csrf(app)

    @app.before_request
    def before_request():
        from cadorsfeed.db import setup_db
        setup_db()


    return app
