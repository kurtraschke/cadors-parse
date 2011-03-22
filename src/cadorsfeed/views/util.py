from uuid import UUID
from datetime import datetime

from pyrfc3339 import generate
from werkzeug import cached_property
from flask import url_for, request
from geoalchemy import PersistentSpatialElement

from cadorsfeed import db
from cadorsfeed.models import DictMixin

def process_report_atom(reports):
    out = []
    for report in reports:
        report.authors = set([narrative.author_name for narrative in report.narrative_parts])
        report.atom_ts = generate(report.last_updated, accept_naive=True)
        out.append(report)
    return out

def json_default(obj):
    if isinstance(obj, DictMixin):
        return dict(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return generate(obj, accept_naive=True)
    if isinstance(obj, PersistentSpatialElement):
        return { "type": "Point", "coordinates": [
                db.session.query(obj.x).scalar(),
                db.session.query(obj.y).scalar()] }
