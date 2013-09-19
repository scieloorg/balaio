from pyramid.renderers import JSONP


class GtwMetaFactory(JSONP):

    def translate_ref(self, ref):
        """
        Translates the url of the resource list
        """
        return [self.request.route_path(obj_type, id=obj_id) for obj_type, obj_id in ref]

    def add_resource_uri(self, value):
        """
        Add the URL of the resource to the own object
        """
        if isinstance(value, (list, tuple)):
            for obj in value:
                obj['resource_uri'] = self.request.path + str(obj['id'])
                for k, v in obj.items():
                    if isinstance(v, list):
                        obj[k] = self.translate_ref(v)
            return value
        else:
            value['resource_uri'] = self.request.path + str(value['id'])
            for k, v in value.items():
                if isinstance(v, list):
                    value[k] = self.translate_ref(v)
            return value

    def add_meta(self, value):
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

            dct_meta['objects'] = self.add_resource_uri(value['objects'])

            return dct_meta
        else:
            return self.add_resource_uri(value)

    def tamper(self, render):
        def wrapper(value, system):
            self.request = system.get('request')
            return render(self.add_meta(value), system)
        return wrapper

    def __call__(self, info):
        render = super(GtwMetaFactory, self).__call__(info)
        render = self.tamper(render)
        return render

GtwFactory = GtwMetaFactory()
