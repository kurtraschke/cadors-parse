from datetime import datetime
import json

from flask import abort, request, redirect, url_for, g
from flask import make_response, render_template, send_file, Module
from flask import current_app as app
import bson.json_util

from cadorsfeed.views.util import Pagination

search = Module(__name__)

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
