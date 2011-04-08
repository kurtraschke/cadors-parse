from flask import render_template, Module

from sqlalchemy import func
from sqlalchemy.sql.expression import select

from cadorsfeed.models import ReportCategory, CadorsReport, category_map
from cadorsfeed.views.util import render_list, prepare_response

category = Module(__name__)


@category.route('/categories/')
def display_categories():
    categories = ReportCategory.query
    categories = categories.add_column(
        select(
            [func.count()],
            category_map.c.category_id == \
                ReportCategory.category_id).select_from(
                    category_map).label('report_count'))

    categories = categories.order_by('report_count DESC',
                                     ReportCategory.text.asc()).all()

    response = make_response(render_template('category_list.html',
                                             categories=categories))
    
    return prepare_response(response, 3600)


@category.route('/category/<int:catid>/', defaults={'page': 1, 'format':'html'})
@category.route('/category/<int:catid>/<int:page>.<any(u"atom", u"json", u"html"):format>')
def display_category_report_list(catid, page, format):
    cat = ReportCategory.query.get_or_404(catid)
    title = "Category: " + cat.text
    pagination = CadorsReport.query.filter(
        CadorsReport.categories.contains(cat)).paginate(page)

    return render_list(pagination, title, format)
