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

    def _positive_int(self, value):
        """
        Converts value to positive int value

        :param value: value can be None, String, Negative, ...
        """
        if isinstance(value, str):
            value = int(value) if value.isdigit() else 0
        if isinstance(value, int):
            return value if value >= 0 else 0
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
        next = self._positive_int(offset) + self._positive_int(limit)
        if next > total:
            return None
        return next

    def _prev_offset(self, offset, limit):
        """
        Calculates the new offset for previous resource_uri

        :param offset: current offset
        :param limit: limit
        """
        if self._positive_int(offset) == 0:
            return None
        if not limit:
            limit = int(self.request.registry.settings.get('http_server', {}).get('limit', 20))

        new_offset = self._positive_int(offset) - self._positive_int(limit)
        if new_offset < 0:
            return None
        return new_offset

    def _query(self, offset=None, limit=None, filters={}):
        #return self.request.current_route_path(_query={'limit': str(limit), 'offset': str(offset)})
        query = filters
        if limit:
            query['limit'] = limit
        if offset >= 0:
            query['offset'] = offset
        return query

    def __resource_uri(self, offset=None, limit=None, filters={}):
        # da erro nos testes
        return self.request.current_route_path(_query=self._query(offset, limit, filters))

    def _resource_uri(self, offset=None, limit=None, filters={}):
        params = [k + '=' + v for k, v in filters.items()]
        if limit:
            params.append('limit=' + str(limit))
        if offset >= 0:
            params.append('offset=' + str(offset))

        if params:
            return self.request.path + '?' + '&'.join(params)
        return self.request.path

    def add_meta(self, value):
        """
        Add information meta on top of the response
        """
        if 'objects' in value:
            dct_meta = {}

            prev_offset = self._prev_offset(value['offset'], value['limit'])
            next_offset = self._next_offset(value['offset'], value['limit'], value['total'])
            dct_meta['meta'] = {
                'limit': self._positive_int(value['limit']),
                'offset': value['offset'],
                'total_count': value['total'],
                'previous': self._resource_uri(prev_offset, value['limit'], value.get('filters', {})) if prev_offset else None,
                'next': self._resource_uri(next_offset, value['limit'], value.get('filters', {})) if next_offset else None,
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
