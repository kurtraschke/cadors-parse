from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException

import redis

from cadorsfeed.utils import local, local_manager, url_map
from cadorsfeed import views


class CadorsFeed(object):

    def __init__(self, host='localhost', port=6379, db=0):
        local.application = self
        self.host = host
        self.port = port
        self.db = db
        local.db = redis.Redis(host=host, port=port, db=db)

    def __call__(self, environ, start_response):
        local.application = self
        local.db = redis.Redis(host=self.host, port=self.port, db=self.db)
        request = Request(environ)
        local.url_adapter = adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            response = handler(request, **values)
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response),
                               [local_manager.cleanup])
