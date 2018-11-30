import os
from compost import exceptions, plugin

class Config(object):
    def __init__(self, raw):
        self._raw = raw

    def build_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("build_dir"))

    def out_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("out_dir"))

    def src_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("src_dir"))

    def data_config(self, filename):
        return self._raw.get("data", {}).get(filename)

    def default_data_plugin(self, type):
        typecfg = self._raw.get("plugins", {}).get("data", {}).get(type, {})
        default = typecfg.get("default")
        if default is None:
            raise exceptions.ConfigurationException("No default provided for '{x}'".format(x=type))
        classpath = typecfg.get("shapes", {}).get(default)
        return plugin.load_class(classpath)

    def data_plugin(self, type, shape):
        classpath = self._raw.get("plugins", {}).get("data", {}).get(type, {}).get("shapes", {}).get(shape)
        if classpath is None:
            raise exceptions.ConfigurationException("No shape '{x}' for type '{y}'".format(x=shape, y=type))
        return plugin.load_class(classpath)


class Data(object):
    def __init__(self, config):
        self._config = config
        self._data_sources = {}

    def add_ref(self, data_path):
        filename = os.path.basename(data_path)
        bits = filename.rsplit(".", 1)
        data_name = bits[0]
        type = bits[1]

        self._data_sources[data_name] = {
            "type" : type,
            "path": data_path
        }

    def get(self, data_name):
        info = self._data_sources.get(data_name)
        if info is None:
            raise exceptions.NoSuchDataSourceException("{x} is not a known data source".format(x=data_name))

        type = info.get("type")
        klazz = self._config.default_data_plugin(type)
        return klazz(info, self._config)


class DataSource(object):
    def __init__(self, info, config):
        self._info = info
        self._config = config

    def __iter__(self):
        pass

    def __next__(self):
        pass

    def shape(self, form):
        klazz = self._config.data_plugin(self._info.get("type"), form)
        if isinstance(self, klazz):
            return self
        return klazz(self._info, self._config)

