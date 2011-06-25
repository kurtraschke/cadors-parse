from flask import Module

from cadorsfeed.views.util import render_file

about = Module(__name__)

@about.route('/')
@about.route('/home')
def homepage():
    return render_file('index.html')

@about.route('/disclaimer')
def disclaimer():
    return render_file('disclaimer.html')

@about.route('/about')
def about_page():
    return render_file('about.html')

@about.route('/privacy')
def privacy_policy():
    return render_file('privacy.html')
