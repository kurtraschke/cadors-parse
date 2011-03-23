from flask import abort, request, redirect, url_for, g, make_response, session, flash, render_template, Module

from sqlalchemy import func
from sqlalchemy.sql.expression import select

from cadorsfeed import db
from cadorsfeed.models import *

category = Module(__name__)

@category.route('/categories/')
def display_categories():
    categories = ReportCategory.query.add_column(
        select([func.count()], 
               category_map.c.category_id==ReportCategory.category_id
               ).select_from(category_map).label('report_count')
        ).order_by('report_count DESC', ReportCategory.text.asc()).all()

    return render_template('category_list.html', categories=categories)

@category.route('/category/<int:catid>/', defaults={'page': 1})
@category.route('/category/<int:catid>/<int:page>')
def display_category_report_list(catid, page):
    cat = ReportCategory.query.get_or_404(catid)

    pagination = CadorsReport.query.filter(CadorsReport.categories.contains(cat)).paginate(page)

    return render_template('list.html', reports=pagination.items,
                           pagination=pagination,
                           endpoint='category.display_category_report_list')
