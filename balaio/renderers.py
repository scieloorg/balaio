from pyramid.renderers import JSONP


class GtwMetaFactory(JSONP):

    def add_resource(self, value, path):
        """
        Add the resource URI to each object
        """
        if 'objects' in value:
            for obj in value['objects']:
                obj['resource_uri'] = path + str(obj['id'])
            return value
        else:
            value['resource_uri'] = path
            return value

    def add_meta(self, value, system):
        """
        Add information meta on top of the response
        """
        if 'objects' in value:
            dct_meta = {}

            dct_meta['meta'] = {
                'limit': value['limit'],
                'offset': value['offset'],
                'total_count': value['total']
            }

            dct_meta['objects'] = self.add_resource(value, system.get('request').path)

            return dct_meta
        else:
            return self.add_resource(value, system.get('request').path)

    def tamper(self, render):
        def wrapper(value, system):
            return render(self.add_meta(value, system), system)
        return wrapper

    def __call__(self, info):
        render = super(GtwMetaFactory, self).__call__(info)
        render = self.tamper(render)
        return render

GtwFactory = GtwMetaFactory()
