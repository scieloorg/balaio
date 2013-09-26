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
                obj['resource_uri'] = self.request.path + '%s/' % str(obj['id'])
                for k, v in obj.items():
                    if isinstance(v, list):
                        obj[k] = self.translate_ref(v)
            return value
        else:
            value['resource_uri'] = self.request.path
            for k, v in value.items():
                if isinstance(v, list):
                    value[k] = self.translate_ref(v)
            return value

    def _new_offset(self, offset, limit, total_count=None):
        if total_count:
            # next
            new_offset = offset + limit
            if new_offset >= total_count:
                return None
        else:
            # previous
            new_offset = offset - limit
            if new_offset < 0:
                return None
        return new_offset

    def _navigation(self, offset, limit, total_count=None):
        new_offset = self._new_offset(offset, limit, total_count)
        if new_offset:
            return self.request.path + '?limit=' + str(limit) + '&offset=' + str(new_offset)
        return None

    def add_meta(self, value):
        """
        Add information meta on top of the response
        """
        if 'objects' in value:
            dct_meta = {}

            dct_meta['meta'] = {
                'limit': value['limit'],
                'offset': value['offset'],
                'total_count': value['total'],
                'previous': self._navigation(value['offset'], value['limit']),
                'next': self._navigation(value['offset'], value['limit'], value['total']),
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
