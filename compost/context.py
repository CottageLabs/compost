class Context(object):
    def __init__(self):
        self._config = None
        self._data = None
        self._runtime_store = {}

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, cfg):
        self._config = cfg

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def remember(self, key, value):
        self._runtime_store[key] = value

    def recall(self, key, default=None):
        return self._runtime_store.get(key, default)

context = Context()