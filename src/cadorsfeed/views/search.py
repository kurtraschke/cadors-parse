from flask import request, render_template, Module

from geoalchemy import WKTSpatialElement, functions
from sqlalchemy import sql, func, or_
import sqlalchemy.types as types

from cadorsfeed.models import CadorsReport, LocationBase, LocationRef
from cadorsfeed.models import Aerodrome, Aircraft

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
                           pagination=pagination)


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

    loc = sql.cast(LocationBase.location, Geography)
    q_loc = sql.cast(location, Geography)

    query = CadorsReport.query.join(LocationRef).join(LocationBase).filter(
        functions.within_distance(loc, q_loc, radius_m))

    if primary:
        query = query.filter(LocationRef.primary == True)

        
    query = query.add_column(functions.distance(loc, q_loc).label('distance'))
    query = query.add_column(
        func.ST_Azimuth(location, 
                        LocationBase.location.RAW) * (180/func.pi()))
    query = query.add_column(LocationBase.name)

    query = query.order_by('distance ASC',
                           CadorsReport.timestamp.desc())

    pagination = query.paginate(page)

    return render_template('sr_loc.html',
                           reports=pagination.items,
                           pagination=pagination,
                           get_direction=get_direction)

def get_direction(degrees):
    degrees = degrees % 360
    
    directions = {0: 'N',
                  45: 'NE',
                  90: 'E',
                  135: 'SE',
                  180: 'S',
                  225: 'SW',
                  270: 'W',
                  315: 'NW',
                  360: 'N'}

    return directions[min(directions.keys(),
                          key=lambda x:abs(x-degrees))]


@search.route('/search/aerodrome')
def search_aerodrome():
    code = request.args['code']
    primary = True if (request.args['primary'] == 'primary') else False
    page = int(request.args.get('page', '1'))

    query = CadorsReport.query.join(LocationRef).join(Aerodrome).filter(
        or_(Aerodrome.icao == code,
            Aerodrome.iata == code,
            Aerodrome.faa == code,
            Aerodrome.tclid == code))

    if primary:
        query = query.filter(LocationRef.primary == True)

    query = query.order_by(CadorsReport.timestamp.desc())

    pagination = query.paginate(page)

    return render_template('list.html', reports=pagination.items,
                           pagination=pagination)

@search.route('/search/flight')
def search_aerodrome():
    operator = request.args['operator']
    flight = request.args.get('flight','')
    page = int(request.args.get('page', '1'))

    query = CadorsReport.query.join(Aircraft).filter(
        Aircraft.flight_number_operator == operator)

    if flight != '':
        query = query.filter(Aircraft.flight_number_flight == int(flight))

    query = query.order_by(CadorsReport.timestamp.desc())

    pagination = query.paginate(page)

    return render_template('list.html', reports=pagination.items,
                           pagination=pagination)
