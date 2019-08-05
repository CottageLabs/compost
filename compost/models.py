import os, json, codecs
from compost import exceptions, plugin, functions, utils

class Config(object):
    def __init__(self, local=None):
        baseconfig = utils.rel2abs(__file__, "baseconfig.json")
        with codecs.open(baseconfig, "r", "utf-8") as f:
            base = json.loads(f.read())
        if local is not None:
            raw = utils.merge_dicts(base, local)
            self._raw = raw
        else:
            self._raw = base

    def build_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("build_dir"))

    def out_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("out_dir"))

    def src_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("src_dir"))

    def base_url(self):
        return self._raw.get("base_url")

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

    def renderer_for_file_suffix(self, suffix):
        for k, v in self._raw.get("plugins", {}).get("renderer", {}).items():
            if suffix in v.get("file_suffixes", []):
                classpath = v.get("class")
                klazz = plugin.load_class(classpath)
                return klazz(k)
        return None

    def renderer_for_inline_tag(self, inline_tag):
        for k, v in self._raw.get("plugins", {}).get("renderer", {}).items():
            if inline_tag == v.get("inline_tag"):
                classpath = v.get("class")
                klazz = plugin.load_class(classpath)
                return klazz(k)
        return None

    def renderer_settings(self, cfg_id):
        return self._raw.get("plugins", {}).get("renderer", {}).get(cfg_id, {}).get("settings", {})

    def util_properties(self, util_name):
        return self._raw.get("utils", {}).get(util_name, {})


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
        self._filter = None
        self._sort = None

    def __iter__(self):
        return self

    def __next__(self):
        pass

    def shape(self, form):
        klazz = self._config.data_plugin(self._info.get("type"), form)
        if isinstance(self, klazz):
            return self
        return klazz(self._info, self._config)

    def filter(self, filter_settings):
        self._filter = filter_settings
        return self

    def include_record(self, record):
        pass

    def sort(self, sort_settings):
        self._sort = sort_settings
        return self


class TableDataSource(DataSource):
    pass

class DictDataSource(DataSource):

    def __init__(self, *args, **kwargs):
        super(DictDataSource, self).__init__(*args, **kwargs)
        self._filter_fn = None
        self._sort_fn_dir = (None, None)

    def filter(self, filter_settings):
        super(DictDataSource, self).filter(filter_settings)
        self._filter_fn = None
        if callable(self._filter):
            self._filter_fn = self._filter
        else:
            self._filter_fn = functions.default_dict_filter(self._filter)
        return self

    def sort(self, sort_settings):
        super(DictDataSource, self).sort(sort_settings)
        self._sort_fn = None
        if callable(self._sort):
            self._sort_fn_dir = self._sort()
        else:
            self._sort_fn_dir = functions.default_dict_sort(self._sort)
        return self

    def include_record(self, record):
        if self._filter_fn is not None:
            return self._filter_fn(record)
        return True


class Renderer(object):
    def __init__(self, cfg_id):
        self._cfg_id = cfg_id

    def render(self, text):
        return text


class RenderConstruct(object):
    def __init__(self, root_renderer):
        self._construct = {
            "renderer" : root_renderer,
            "content" : []
        }
        self._stack = [self._construct["content"]]

    def __str__(self):
        return json.dumps(self._construct, indent=2,
                          default=lambda o: o.__name__ if hasattr(o, "__name__") else o)

    def append(self, text):
        self._stack[-1].append({
            "raw" : text
        })

    def push(self, renderer):
        self._stack[-1].append({
            "renderer" : renderer,
            "content" : []
        })
        self._stack.append(self._stack[-1][-1]["content"])

    def pop(self):
        if len(self._stack) > 1:
            del self._stack[-1]

    def depth(self):
        return len(self._stack)

    def render(self):
        def recurse(node):
            renderer = node.get("renderer")
            contents = node.get("content", [])
            text = ""
            for c in contents:
                if "raw" in c:
                    text += c["raw"]
                if "renderer" in c:
                    text += recurse(c)
            return renderer.render(text)

        return recurse(self._construct)


