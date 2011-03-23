from flask import request, render_template, Module

from geoalchemy import WKTSpatialElement, functions
from sqlalchemy import sql, func
import sqlalchemy.types as types

from cadorsfeed.models import CadorsReport, Location

search = Module(__name__)


@search.route('/search/')
def search_form():
    return render_template('search.html')


@search.route('/search/text')
def search_text():
    terms = request.args['q']
    page = int(request.args.get('page', '1'))

    query = CadorsReport.query.filter(
        'cadors_report.narrative_agg_idx_col @@ plainto_tsquery(:terms)')

    query = query.params(terms=terms)

    query = query.add_column(
        func.ts_headline('pg_catalog.english',
                         CadorsReport.narrative_agg,
                         func.plainto_tsquery(terms),
                         '''MaxFragments=5,
                            MinWords=15,
                            MaxWords=20,
                            FragmentDelimiter=|||,
                            StartSel="<b>",
                            StopSel = "</b>"''',
                         type_=types.Unicode))

    query = query.order_by(
        'ts_rank_cd(narrative_agg_idx_col, plainto_tsquery(:terms)) DESC')

    pagination = query.paginate(page)

    return render_template('sr_text.html', reports=pagination.items,
                           pagination=pagination,
                           endpoint='search.search_text')


class Geography(types.TypeEngine):
    def _compiler_dispatch(self, thing):
        return 'geography'


@search.route('/search/location')
def search_location():
    latitude = request.args['latitude']
    longitude = request.args['longitude']
    radius = int(request.args['radius'])
    primary = True if (request.args['primary'] == 'primary') else False
    page = int(request.args.get('page', '1'))

    radius_m = radius * 1000

    wkt = "POINT(%s %s)" % (longitude, latitude)
    location = WKTSpatialElement(wkt)

    loc = sql.cast(Location.location, Geography)
    q_loc = sql.cast(location, Geography)

    query = CadorsReport.query.join(Location).filter(
        functions.within_distance(loc, q_loc, radius_m))

    if primary:
        query = query.filter(Location.primary == True)

    query = query.add_column(functions.distance(loc, q_loc).label('distance'))
    #query = query.add_column((functions.azimuth(loc, q_loc) * 180)/func.pi())

    query = query.order_by('distance ASC',
                           CadorsReport.timestamp.desc())

    pagination = query.paginate(page)

    return render_template('sr_loc.html', reports=pagination.items,
                           pagination=pagination,
                           endpoint='search.search_location')
