from flask import Module

from cadorsfeed.views.util import render_file

static = Module(__name__)

@static.route('/')
@static.route('/home')
def homepage():
    return render_file('index.html')

@static.route('/disclaimer')
def disclaimer():
    return render_file('disclaimer.html')

@static.route('/about')
def about_page():
    return render_file('about.html')

@static.route('/privacy')
def privacy_policy():
    return render_file('privacy.html')
