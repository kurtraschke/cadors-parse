from flask import url_for

from sqlalchemy import func, DDL
from sqlalchemy.orm import class_mapper, ColumnProperty, deferred
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy

from geoalchemy import GeometryColumn, Point, GeometryDDL
from geoalchemy.postgis import PGComparator

from cadorsfeed import db
from cadorsfeed.unique import unique_constructor


class DictMixin(object):
    #based on
    #http://blog.mitechie.com/2010/04/01/hacking-the-sqlalchemy-base-class/
    def __iter__(self):
        d = {}
        for c in [p.key for p in \
                  class_mapper(self.__class__).iterate_properties \
                  if isinstance(p, ColumnProperty)]:
            value = getattr(self, c)
            yield(c, value)

report_map = db.Table(
    'report_map', db.Model.metadata,
    db.Column('reportmap_id', db.Integer(), primary_key=True),
    db.Column('daily_report_id', db.Integer(),
              db.ForeignKey('daily_report.daily_report_id'), index=True),
    db.Column('report_id', db.CHAR(9),
              db.ForeignKey('cadors_report.cadors_number'), index=True))


class DailyReport(db.Model, DictMixin):
    daily_report_id = db.Column(db.Integer(), primary_key=True)
    report_date = db.Column(db.DateTime(), unique=True, index=True)
    fetch_timestamp = db.Column(db.DateTime())
    parse_timestamp = db.Column(db.DateTime())
    report_html = deferred(db.Column(db.LargeBinary()))
    reports = db.relationship("CadorsReport", secondary=report_map,
                              backref='daily_reports')
    __mapper_args__ = {'order_by': report_date.desc()}

    @property
    def last_updated(self):
        return db.session.query(func.max(NarrativePart.date)).join(
            CadorsReport).join(report_map).join(
            DailyReport).filter(
                DailyReport.report_date == self.report_date).scalar()

    @staticmethod
    def first():
        return DailyReport.query.order_by(DailyReport.report_date.asc()).first()

    @staticmethod
    def last():
        return DailyReport.query.order_by(DailyReport.report_date.desc()).first()

    def link(self, full=False, **kwargs):
        endpoint = 'daily_report.do_daily_report' if full is False \
            else 'daily_report.daily_report_full'
        return url_for(endpoint,
                       year=self.report_date.year,
                       month=self.report_date.month,
                       day=self.report_date.day,
                       **kwargs)

category_map = db.Table(
    'category_map', db.Model.metadata,
    db.Column('catmap_id', db.Integer(), primary_key=True),
    db.Column('report_id', db.CHAR(9),
              db.ForeignKey('cadors_report.cadors_number'), index=True),
    db.Column('category_id', db.Integer(),
              db.ForeignKey('report_category.category_id'), index=True))


class CadorsReport(db.Model, DictMixin):
    cadors_number = db.Column(db.CHAR(9), primary_key=True)
    uuid = db.Column(UUID(as_uuid=True))
    timestamp = db.Column(db.DateTime(), index=True)
    occurrence_type = db.Column(db.Unicode())
    fatalities = db.Column(db.Integer())
    injuries = db.Column(db.Integer())
    aerodrome_name = db.Column(db.Unicode())
    tclid = db.Column(db.CHAR(4))
    location = db.Column(db.Unicode())
    province = db.Column(db.Unicode())
    nav_canada_aor = db.Column(db.Unicode())
    tsb_class = db.Column(db.Integer())
    tsb_number = db.Column(db.Unicode())
    reported_by = db.Column(db.Unicode())
    region = db.Column(db.Unicode())
    world_area = db.Column(db.Unicode())
    day_night = db.Column(db.Unicode())
    narrative_agg = deferred(db.Column(db.UnicodeText()))
    categories = db.relationship("ReportCategory", backref="reports",
                                 secondary=category_map,
                                 cascade="all, delete")
    aircraft = db.relationship("Aircraft", backref="report",
                               cascade="all, delete, delete-orphan")
    narrative_parts = db.relationship("NarrativePart", backref="report",
                                      cascade="all, delete, delete-orphan")
    locationrefs = db.relationship("LocationRef", backref="report",
                                   cascade="all, delete, delete-orphan")

    locations = association_proxy('locationrefs', 'location')

    __mapper_args__ = {'order_by': timestamp.desc()}

    @property
    def last_updated(self):
        return db.session.query(
            func.max(NarrativePart.date)).with_parent(self).scalar()

    @property
    def timestamp_html(self):
        return self.timestamp.strftime("%Y&#8209;%m&#8209;%d&nbsp;%H%M&nbsp;Z")

    def link(self, **kwargs):
        return url_for('report.display_report',
                       report=self.cadors_number,
                       **kwargs)


@unique_constructor(db.session,
                    lambda text: text,
                    lambda query, text: query.filter(
        ReportCategory.text == text))
class ReportCategory(db.Model, DictMixin):
    category_id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.Unicode(), index=True, unique=True)


class Aircraft(db.Model, DictMixin):
    aircraft_id = db.Column(db.Integer(), primary_key=True)
    cadors_number = db.Column(db.CHAR(9),
                              db.ForeignKey('cadors_report.cadors_number'),
                              index=True)
    category = db.Column(db.Unicode())
    engine_model = db.Column(db.Unicode())
    engine_make = db.Column(db.Unicode())
    make = db.Column(db.Unicode())
    model = db.Column(db.Unicode())
    damage = db.Column(db.Unicode())
    reg_country = db.Column(db.Unicode())
    owner = db.Column(db.Unicode())
    flight_number = db.Column(db.Unicode())
    flight_number_operator = db.Column(db.Unicode(), index=True)
    flight_number_flight = db.Column(db.Integer(), index=True)
    flight_phase = db.Column(db.Unicode())
    year = db.Column(db.Integer())
    operator = db.Column(db.Unicode())
    amateur_built = db.Column(db.Unicode())
    gear_type = db.Column(db.Unicode())
    engine_type = db.Column(db.Unicode())
    operator_type = db.Column(db.Unicode())


class NarrativePart(db.Model, DictMixin):
    narrative_part_id = db.Column(db.Integer(), primary_key=True)
    cadors_number = db.Column(db.CHAR(9),
                              db.ForeignKey('cadors_report.cadors_number'),
                              index=True)
    author_name = db.Column(db.Unicode())
    name = db.synonym('author_name')
    date = db.Column(db.DateTime())
    narrative_text = deferred(db.Column(db.UnicodeText()))
    narrative_xml = db.Column(db.UnicodeText())
    narrative_html = db.Column(db.UnicodeText())
    further_action = db.Column(db.Unicode())
    opi = db.Column(db.Unicode())

    __mapper_args__ = {'order_by': date.asc()}


class LocationRef(db.Model):
    locref_id = db.Column(db.Integer(), primary_key=True)
    cadors_number = db.Column(db.CHAR(9),
                              db.ForeignKey('cadors_report.cadors_number'),
                              index=True)
    location_id = db.Column(db.Integer(),
                            db.ForeignKey('location.location_id'),
                            index=True)
    primary = db.Column(db.Boolean(), default=False, nullable=False)


class LocationBase(db.Model, DictMixin):
    __tablename__ = 'location'

    location_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    url = db.Column(db.String())
    location = GeometryColumn(Point(2), comparator=PGComparator)
    discriminator = db.Column('type', db.String(10))
    __mapper_args__ = {'polymorphic_on': discriminator}
    locationrefs = db.relationship("LocationRef", backref="location",
                                   cascade="all, delete, delete-orphan")

    @property
    def latitude(self):
        return db.session.scalar(self.location.y)

    @property
    def longitude(self):
        return db.session.scalar(self.location.x)

    @property
    def kml(self):
        return db.session.scalar(self.location.kml)

GeometryDDL(LocationBase.__table__)

@unique_constructor(db.session,
                    lambda location: db.session.scalar(location.wkt),
                    lambda query, location: query.filter(
        Location.location == location))
class Location(LocationBase):
    __mapper_args__ = {'polymorphic_identity':'location'}


class Aerodrome(LocationBase):
    __mapper_args__ = {'polymorphic_identity': 'aerodrome'}
    icao = db.Column(db.CHAR(4), unique=True, index=True)
    iata = db.Column(db.CHAR(3), unique=True, index=True)
    faa = db.Column(db.CHAR(3), unique=True, index=True)
    tclid = db.Column(db.CHAR(4), unique=True, index=True)
    lid = db.synonym('tclid')
    airport = db.synonym('url')
    blacklist = db.Column(db.Boolean(), nullable=False, default=False)



DDL('''ALTER TABLE cadors_report ADD COLUMN
       narrative_agg_idx_col tsvector''').execute_at("after-create",
                                                     CadorsReport.__table__)

DDL('''CREATE INDEX narrative_agg_idx ON cadors_report
       USING gin(narrative_agg_idx_col)''').execute_at("after-create",
                                                       CadorsReport.__table__)

DDL('''CREATE OR REPLACE FUNCTION
       update_narrative_index(cadors_number_p varchar) RETURNS void AS $$
BEGIN
        UPDATE cadors_report SET narrative_agg =
               array_to_string(
                 (SELECT array_agg(narrative_text)
                         FROM narrative_part
                         WHERE narrative_part.cadors_number = cadors_number_p
                         GROUP BY narrative_part.cadors_number
                 ),' ') WHERE cadors_number = cadors_number_p;

        UPDATE cadors_report SET narrative_agg_idx_col =
               to_tsvector(narrative_agg)
               WHERE cadors_report.cadors_number = cadors_number_p;
END;
$$ LANGUAGE plpgsql;''').execute_at("after-create",
                                    NarrativePart.__table__)

DDL('''CREATE OR REPLACE FUNCTION process_narrative_update()
       RETURNS TRIGGER AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM update_narrative_index(OLD.cadors_number);
        ELSIF (TG_OP = 'UPDATE') THEN
            PERFORM update_narrative_index(NEW.cadors_number);
        ELSIF (TG_OP = 'INSERT') THEN
            PERFORM update_narrative_index(NEW.cadors_number);
        END IF;
        RETURN NULL;
    END;
$$ LANGUAGE plpgsql;''').execute_at("after-create",
                                    NarrativePart.__table__)

DDL('''CREATE TRIGGER narrative_update
       AFTER INSERT OR UPDATE OR DELETE ON narrative_part
       FOR EACH ROW EXECUTE PROCEDURE process_narrative_update();
    ''').execute_at("after-create",
                    NarrativePart.__table__)
