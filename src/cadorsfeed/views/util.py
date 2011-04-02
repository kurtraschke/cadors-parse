from uuid import UUID
from datetime import datetime

from pyrfc3339 import generate
from geoalchemy import PersistentSpatialElement

from cadorsfeed import db, modified_url_for
from cadorsfeed.models import CadorsReport, ReportCategory, Aircraft
from cadorsfeed.models import LocationBase, NarrativePart


def process_report_atom(reports):
    out = []
    for report in reports:
        report.authors = set([narrative.author_name for narrative \
                                  in report.narrative_parts])
        report.atom_ts = generate(report.last_updated, accept_naive=True)
        out.append(report)
    return out


def render_list(pagination, title, format):
    if format == 'json':
        response = make_response(json.dumps(
                {'reports': pagination.items},
                indent=None if request.is_xhr else 2,
                default=json_default))
        response.mimetype = "application/json"
    elif format == 'atom':
        reports = process_report_atom(pagination.items)
        feed_timestamp = generate(max(pagination.items,
                                      key=lambda r:r.last_updated).last_updated,
                                  accept_naive=True)
        next = modified_url_for(page=pagination.next_num,
                                _external=True
                                ) if pagination.has_next else False
        prev = modified_url_for(page=pagination.prev_num,
                                _external=True
                                ) if pagination.has_prev else False

        response = make_response(
            render_template('feed.xml',
                            reports=reports,
                            feed_timestamp=feed_timestamp,
                            next=next,
                            prev=prev,
                            title=title))
        response.mimetype = "application/atom+xml"
    elif format == 'html':
        response = make_response(render_template('list.html',
                                                 reports=pagination.items,
                                                 pagination=pagination,
                                                 title=title))
    else:
        abort(400)

    response.add_etag()
    response.make_conditional(request)
    return response


def json_default(obj):
    if isinstance(obj, CadorsReport):
        result = dict(obj)
        del result['narrative_agg']
        result['categories'] = obj.categories
        result['aircraft'] = obj.aircraft
        result['narrative_parts'] = obj.narrative_parts
        result['locations'] = list(obj.locations)
        return result
    if isinstance(obj, ReportCategory):
        return obj.text
    if isinstance(obj, Aircraft):
        result = dict(obj)
        del result['aircraft_id']
        del result['cadors_number']
        return result
    if isinstance(obj, NarrativePart):
        result = dict(obj)
        del result['cadors_number']
        del result['narrative_html']
        del result['narrative_part_id']
        return result
    if isinstance(obj, LocationBase):
        result = dict(obj)
        del result['location_id']
        del result['discriminator']
        if 'blacklist' in result.keys():
            del result['blacklist']
        return result
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return generate(obj, accept_naive=True)
    if isinstance(obj, PersistentSpatialElement):
        return {"type": "Point",
                "coordinates": [
                db.session.query(obj.x).scalar(),
                db.session.query(obj.y).scalar()]}
