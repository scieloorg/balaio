from pyramid.renderers import JSONP
from pyramid.url import current_route_url


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

    def _int(self, value):
        """
        Converts value to int and positive value

        :param value: value can be None, String, Negative, ...
        """

        if not value:
            return 0
        if isinstance(value, str):
            value = int(value) if value.isdigit() else 0
        if value < 0:
            return 0
        return value

    def _next_offset(self, offset, limit):
        """
        Calculates the offset for next resource_uri

        :param offset: current offset
        :param total_count: it limits the next offset
        :param limit: limit
        """
        if not limit:
            limit = self.request.registry.settings.get('http_server', {}).get('limit', 20)
        return self._int(offset) + self._int(limit)

    def _prev_offset(self, offset, limit):
        """
        Calculates the new offset for previous resource_uri

        :param offset: current offset
        :param limit: limit
        """
        if self._int(offset) == 0:
            return None
        if not limit:
            limit = self.request.registry.settings.get('http_server', {}).get('limit', 20)
        new_offset = self._int(offset) - self._int(limit)
        if new_offset < 0:
            return None
        return new_offset

    def _resource_uri_(self, offset=None, limit=None):
        return self.request.current_route_url(_query={'limit': limit, 'offset': offset}, _route_name='')

    def _resource_uri(self, offset=None, limit=None):
        #return self.request.current_route_path(_query={'limit': str(limit), 'offset': str(offset)})
        r = self.request.path
        param = []
        if limit:
            param.append('limit=' + str(limit))
        if offset >= 0:
            param.append('offset=' + str(offset))
        if param:
            r += '?' + '&'.join(param)
        return r

    def add_meta(self, value):
        """
        Add information meta on top of the response
        """
        if 'objects' in value:
            dct_meta = {}

            _prev_offset = self._prev_offset(value['offset'], value['limit'])

            dct_meta['meta'] = {
                'limit': value['limit'],
                'offset': value['offset'],
                'total_count': value['total'],
                'previous': self._resource_uri(_prev_offset, value['limit']) if _prev_offset else None,
                'next': self._resource_uri(self._next_offset(value['offset'], value['limit']), value['limit']),
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
