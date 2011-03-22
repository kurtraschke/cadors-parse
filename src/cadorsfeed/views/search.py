from datetime import datetime
import json

from flask import abort, request, redirect, url_for, g
from flask import make_response, render_template, send_file, Module
from flask import current_app as app

from geoalchemy import WKTSpatialElement, functions
from sqlalchemy import sql
import sqlalchemy.types as types

from cadorsfeed import db
from cadorsfeed.models import *

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
                         type_= types.Unicode)) 
    
    query = query.order_by(
        'ts_rank_cd(narrative_agg_idx_col, plainto_tsquery(:terms)) DESC'
        )

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
    location  = WKTSpatialElement(wkt)

    loc = sql.cast(Location.location, Geography)
    q_loc = sql.cast(location, Geography)

    query = CadorsReport.query.join(Location).filter(
        functions.within_distance(loc, q_loc, radius_m)
        )
    
    if primary:
        query = query.filter(Location.primary==True)

    query = query.add_column(functions.distance(loc, q_loc).label('distance'))
    #query = query.add_column((functions.azimuth(loc, q_loc) * 180)/func.pi())

    query = query.order_by('distance ASC',
                           CadorsReport.timestamp.desc())

    pagination = query.paginate(page)

    return render_template('sr_loc.html', reports=pagination.items,
                           pagination=pagination,
                           endpoint='search.search_location')




'''
@search.route('/search/', defaults={'page':1})
@search.route('/search/<int:page>')
def search_reports(page):
    
    radius = float(request.values['radius']) / 6378.1
    latitude = float(request.values['latitude'])
    longitude = float(request.values['longitude'])

    locations = g.mdb.locations.find({"location" : 
                                       {"$within" : 
                                        {"$centerSphere" : 
                                         [[longitude,
                                           latitude],
                                          radius]
                                         }
                                        }
                                       }, {"cadors_number": 1})

    report_ids = list(set([location['cadors_number'] for location in locations]))

    query = {"cadors_number": {"$in": report_ids}}
    
    pagination = Pagination(g.mdb.reports, query, 20, page, 'search.search_reports')

    return render_template('list.html', reports=pagination.entries,
                           pagination=pagination)
'''
