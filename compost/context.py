class Context(object):
    def __init__(self):
        self._config = None
        self._data = None

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

context = Context()