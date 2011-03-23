#From http://www.sqlalchemy.org/trac/wiki/UsageRecipes/UniqueObject


def unique_constructor(scoped_session, hashfunc, queryfunc):
    def decorate(cls):
        def _null_init(self, *arg, **kw):
            pass

        def __new__(cls, bases, *arg, **kw):
            # no-op __new__(), called
            # by the loading procedure
            if not arg and not kw:
                return object.__new__(cls)

            session = scoped_session()
            cache = getattr(session, '_unique_cache', None)
            if cache is None:
                session._unique_cache = cache = {}

            key = (cls, hashfunc(*arg, **kw))
            if key in cache:
                return cache[key]
            else:
                # disabling autoflush is optional here.
                # this tends to be an awkward place for
                # flushes to occur, however, as we're often
                # inside a constructor.
                with no_autoflush(session):
                    q = session.query(cls)
                    q = queryfunc(q, *arg, **kw)
                    obj = q.first()
                    if not obj:
                        obj = object.__new__(cls)
                        obj._init(*arg, **kw)
                        session.add(obj)
                cache[key] = obj
                return obj

        cls._init = cls.__init__
        cls.__init__ = _null_init
        cls.__new__ = classmethod(__new__)
        return cls

    return decorate


class no_autoflush(object):
    """Temporarily disable autoflush.

    See http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DisableAutoflush
    """
    def __init__(self, session):
        self.session = session
        self.autoflush = session.autoflush

    def __enter__(self):
        self.session.autoflush = False

    def __exit__(self, type, value, traceback):
        self.session.autoflush = self.autoflush
