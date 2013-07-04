import json
import urllib2
from StringIO import StringIO


def etree_nodes_value(etree, xpath):
    """
    Returns text of a given ``xpath`` of ``etree``
    """
    return '\n'.join([node.text for node in etree.findall(xpath)])


class Manager(object):
    """
    Interface for SciELO API
    """
    _main = 'MAIN/QUERY?username=USERNAME&api_key=API_KEY&format=json'

    def __init__(self, api_url='http:/????', username='', api_key=''):
        super(Manager, self).__init__()
        self.api_params['USERNAME'] = username
        self.api_params['API_KEY'] = api_key
        self.api_params['MAIN'] = api_url

        for key, param in self.api_params.items():
            self._main = self._main.replace(key, param)

    def do_query(self, query, params={}):
        """
        Consulta SciLO Manager API
        Returns JSON
        """
        try:
            r = urllib2.open(self._main.replace('QUERY', query) + '&'.join([key + '=' + value for key, value in params.items()])).read()
        except:
            r = '{}'
        return json.load(StringIO(r))

    def _item_id(self, query, data_label, match_value):
        """
        Find in all an item which ``data_label`` has a value that matches ``match_value``
        (esse metodo seria desnecessario se na api estivesse search)
        Returns item id
        """
        item_id = None
        all_items = json.load(self.do_query(query))

        meta = all_items.get('meta', {})
        total = meta.get('total_count', 0)
        offset = meta.get('offset', 0)
        limit = meta.get('limit', 0)

        found = [o for o in all_items.get('objects', {}) if o.get(data_label, '') == match_value]
        while found is [] and offset < total:
            offset += limit
            all_items = json.load(self.do_query(query, {'offset': offset}))
            found = [o for o in all_items.get('objects', {}) if o.get(data_label, '') == match_value]

        if not found is []:
            item_id = found[0].get('id', None)
        return item_id

    def journal(self, value, attribute='id'):
        item_id = value if attribute == 'id' else self._item_id('journals', attribute, value)
        return self.do_query('journals/' + item_id + '/')
