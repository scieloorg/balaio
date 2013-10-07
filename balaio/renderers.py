from pyramid.renderers import JSONP


class GtwMetaFactory(JSONP):

    def add_resource_uri(self, obj):
        """
        Add the URL to all resources of an object
        """
        obj['resource_uri'] = self.request.path + '%s/' % str(obj['id'])
        if 'related_resources' in obj:
            for label, route_name, id_list in obj['related_resources']:
                obj[label] = [self.request.route_path(route_name, id=str(item_id)) for item_id in id_list]
            del obj['related_resources']
        return obj

    def _positive_int_or_zero(self, value):
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
        next = self._positive_int_or_zero(offset) + self._positive_int_or_zero(limit)
        if next > total:
            return None
        return next

    def _prev_offset(self, offset, limit):
        """
        Calculates the new offset for previous resource_uri

        :param offset: current offset
        :param limit: limit
        """
        if self._positive_int_or_zero(offset) == 0:
            return None
        if not limit:
            limit = int(self.request.registry.settings.get('http_server', {}).get('limit', 20))

        new_offset = self._positive_int_or_zero(offset) - self._positive_int_or_zero(limit)
        if new_offset < 0:
            return None
        return new_offset

    def _current_resource_path(self, filters, offset=None, limit=None):
        """
        Returns the current resource path excluding filters containing ``None`` as value.

        :param filters: a dict to be returned as querystring params.
        :param offset: (optional) an int. Default is ``None``.
        :param limit: (optional) an int. Default is ``None``.
        """
        filters.update({'offset': offset})
        filters.update({'limit': limit})
        return self.request.current_route_path(_query={k: v for k, v in filters.items() if v})

    def format_response(self, data):
        """
        Format response
        To a single document, add resource_uri to the object
        To a set of documents, add meta and add resource_uri to all objects

        """
        if 'objects' in data:
            dct_meta = {}
            prev_offset = self._prev_offset(data['offset'], data['limit'])
            next_offset = self._next_offset(data['offset'], data['limit'], data['total'])

            dct_meta['meta'] = {
                'limit': self._positive_int_or_zero(data['limit']),
                'offset': data['offset'],
                'total': data['total'],
                'previous': self._current_resource_path(data.get('filters', {}), prev_offset, data['limit']) if prev_offset else None,
                'next': self._current_resource_path(data.get('filters', {}), next_offset, data['limit']) if next_offset else None,
            }
            dct_meta['objects'] = [self.add_resource_uri(obj) for obj in data['objects']]
            return dct_meta
        else:
            return self.add_resource_uri(data)

    def tamper(self, render):
        def wrapper(value, system):
            self.request = system.get('request')
            return render(self.format_response(value), system)
        return wrapper

    def __call__(self, info):
        render = super(GtwMetaFactory, self).__call__(info)
        render = self.tamper(render)
        return render

GtwFactory = GtwMetaFactory()
