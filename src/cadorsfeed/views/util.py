from pyrfc3339 import generate
from werkzeug import cached_property
from flask import url_for, request


def process_report_atom(reports):
    out = []
    for report in reports:
        report['authors'] = set([narrative['name'] for narrative in report['narrative']])
        report['atom_ts'] = generate(report['timestamp'], accept_naive=True)
        out.append(report)
    return out

class Pagination(object):

    def __init__(self, db, query, per_page, page, endpoint, sort=None):
        self.db = db
        self.query = query
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint
        self.sort = sort

    @cached_property
    def count(self):
        return self.db.find(self.query).count()

    @cached_property
    def entries(self):
        cursor = self.db.find(self.query).skip(
            (self.page - 1) * self.per_page).limit(self.per_page)
        if self.sort:
            cursor.sort(self.sort)
        return cursor

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=3, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and \
                         num < self.page + right_current) or \
                         num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
        
    def url_for_page(self, page):
        args =  request.args.to_dict(flat=True)
        args.update(request.view_args.copy())
        args['page'] = page
        return url_for(self.endpoint, **args)

    has_previous = property(lambda x: x.page > 1)
    has_next = property(lambda x: x.page < x.pages)
    previous = property(lambda x: x.url_for_page(page=x.page - 1))
    next = property(lambda x: x.url_for_page(page=x.page + 1))
    pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)
