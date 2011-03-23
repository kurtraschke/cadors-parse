from decimal import *

#from bson.son import SON

setcontext(ExtendedContext)
precision = Decimal('0.000001')


class LocationStore(object):
    def __init__(self):
        self.locations = {}

    def add(self, latitude, longitude, name, url=None, primary=False):
        latitude = makedecimal(latitude).quantize(precision).normalize()
        longitude = makedecimal(longitude).quantize(precision).normalize()

        for location, data in self.locations.iteritems():
            (other_lat, other_lon) = location
            if latitude == other_lat and longitude == other_lon:
                if url is not None:
                    data['url'] = url
                if primary is True:
                    data['primary'] = True
                break
        else:
            #new location
            self.locations[(latitude, longitude)] = {'name': name,
                                                     'primary': primary}
            if url is not None:
                self.locations[(latitude, longitude)]['url'] = url

    def to_list(self):
        out = []
        for location, data in self.locations.iteritems():
            (data['latitude'], data['longitude']) = location
            out.append(data)
        return out


def makedecimal(value):
    if isinstance(value, float):
        return Decimal(str(value))
    else:
        return Decimal(value)
