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

    def format_response(self, data):
        """
        Format response
        To a single document, add resource_uri to the object
        To a set of documents, add meta and add resource_uri to all objects

        :param data: query result
        """
        if 'objects' in data:
            dct_meta = {}

            dct_meta['meta'] = {
                'limit': data['limit'],
                'offset': data['offset'],
                'total_count': data['total']
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
