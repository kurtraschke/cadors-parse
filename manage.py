#!/usr/bin/env python
from werkzeug import script


def make_app():
    from cadorsfeed.application import CadorsFeed
    return CadorsFeed()


def make_shell():
    from cadorsfeed import utils
    application = make_app()
    return locals()

action_runserver = script.make_runserver(make_app, use_reloader=True, hostname='')
action_shell = script.make_shell(make_shell)

script.run()
