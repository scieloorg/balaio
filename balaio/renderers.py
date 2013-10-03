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

    def _N(self, value):
        """
        Returns a natural number (0, 1, 2, ...)

        :param value: value can be None, String, Negative, ...
        """
        try:
            num = int(value)
            return num if num >= 0 else 0
        except (TypeError, ValueError) as e:
            return 0

    def _next_offset(self, offset, limit, total):
        """
        Calculates the offset for next resource_uri

        :param offset: current offset
        :param limit: limit
        :param total: it limits the next offset
        """
        if not limit:
            limit = self.request.registry.settings.get('http_server', {}).get('limit', 20)
        next = self._N(offset) + self._N(limit)
        if next > total:
            return None
        return next

    def _prev_offset(self, offset, limit):
        """
        Calculates the new offset for previous resource_uri

        :param offset: current offset
        :param limit: limit
        """
        if self._N(offset) == 0:
            return None
        if not limit:
            limit = int(self.request.registry.settings.get('http_server', {}).get('limit', 20))

        new_offset = self._N(offset) - self._N(limit)
        if new_offset < 0:
            return None
        return new_offset

    def _resource_uri(self, filters, offset=None, limit=None):
        # a linha abaixo da erro nos testes
        #return self.request.current_route_path(_query=self._query(filters, offset, limit))
        import urllib
        filters.update({'offset': offset})
        filters.update({'limit': limit})
        q = urllib.urlencode({k: v for k, v in filters.items() if v})
        return self.request.path + '?' + q if q else self.request.path

    def add_meta(self, value):
        """
        Add information meta on top of the response
        """
        if 'objects' in value:
            dct_meta = {}

            prev_offset = self._prev_offset(value['offset'], value['limit'])
            next_offset = self._next_offset(value['offset'], value['limit'], value['total'])
            dct_meta['meta'] = {
                'limit': self._N(value['limit']),
                'offset': value['offset'],
                'total_count': value['total'],
                'previous': self._resource_uri(value.get('filters', {}), prev_offset, value['limit']) if prev_offset else None,
                'next': self._resource_uri(value.get('filters', {}), next_offset, value['limit']) if next_offset else None,
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
