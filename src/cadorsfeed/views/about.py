from flask import Module, make_response, render_template, request

about = Module(__name__)

@about.route('/')
def homepage():
    return render_file('index.html')

@about.route('/disclaimer')
def disclaimer():
    return render_file('disclaimer.html')

@about.route('/about')
def about_page():
    return render_file('about.html')

def render_file(template):
    response = make_response(render_template(template))
    response.add_etag()
    response.make_conditional(request)
    return response
