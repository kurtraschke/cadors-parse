import redis
from pymongo import Connection
from pymongo.son_manipulator import AutoReference, NamespaceInjector
from gridfs import GridFS
from flask import g, current_app as app

def setup_db():
        #g.db = redis.Redis(host=app.config['REDIS_HOST'],
        #                port=app.config['REDIS_PORT'],
        #                db=app.config['REDIS_DB'])
        g.mongo = Connection()
        g.mdb = g.mongo.cadorsdb
        g.mdb.add_son_manipulator(NamespaceInjector())
        g.mdb.add_son_manipulator(AutoReference(g.mdb))
        g.fs = GridFS(g.mdb)
