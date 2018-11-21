import os

class Config(object):
    def __init__(self, raw):
        self._raw = raw

    def build_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("build_dir"))

    def out_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("out_dir"))

    def src_dir(self):
        return os.path.join(self._raw.get("base_dir"), self._raw.get("src_dir"))