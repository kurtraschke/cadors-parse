from werkzeug import Local, LocalManager
from werkzeug.routing import Map, Rule

local = Local()
local_manager = LocalManager([local])
application = local('application')
db = local('db')

url_map = Map()

def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate

def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)

