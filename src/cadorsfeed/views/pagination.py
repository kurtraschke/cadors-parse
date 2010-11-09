from werkzeug import cached_property
from flask import url_for

class Pagination(object):

    def __init__(self, db, key, per_page, page, endpoint):
        self.db = db
        self.query = key
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint

    @cached_property
    def count(self):
        return self.db.zcard(self.query)

    @cached_property
    def entries(self):
        start = (self.page - 1) * self.per_page
        return self.db.zrevrange(self.query, start, (start + self.per_page) - 1)

    has_previous = property(lambda x: x.page > 1)
    has_next = property(lambda x: x.page < x.pages)
    previous = property(lambda x: url_for(x.endpoint, page=x.page - 1))
    next = property(lambda x: url_for(x.endpoint, page=x.page + 1))
    pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)
