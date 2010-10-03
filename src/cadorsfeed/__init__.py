from flask import Flask
app = Flask(__name__)
app.add_url_rule('/favicon.ico', 'favicon', redirect_to = '/static/favicon.ico')

import cadorsfeed.views
