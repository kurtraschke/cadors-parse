from functools import wraps

extensions = {}
EXTENSION_NS = 'urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd'


def register(func):
    @wraps(func)
    def wrapper(*args):
        return func(*args[1:])
    extensions[(EXTENSION_NS, func.__name__)] = wrapper
    return func


@register
def strip_nbsp(to_strip):
    if isinstance(to_strip, list):
        if len(to_strip) == 0:
            return None
        to_strip = stripout(to_strip)
    return to_strip.rstrip(u'\xa0')


def stripout(things):
    assert len(things) == 1, things
    return things[0]
