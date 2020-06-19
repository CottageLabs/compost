from compost import models
import json

class DictJSONDataSource(models.DictDataSource):
    def __init__(self, info, config):
        super(DictJSONDataSource, self).__init__(info, config)
        if "shapes" not in self._info:
            self._info["shapes"] = {}
        self._info["shapes"]["dict"] = {}

    def __iter__(self):
        local_data = self._info["shapes"]["dict"]
        if "data" in local_data:
            return self

        self._load_raw()

        return self

    def __next__(self):
        return self.next()

    def get(self, key, default=None):
        self._load_raw()
        return super(DictJSONDataSource, self).get(key, default)

    def items(self):
        self._load_raw()
        return super(DictJSONDataSource, self).items()

    def __getitem__(self, item):
        self._load_raw()
        return super(DictJSONDataSource, self).items()

    def next(self):
        pass

    def _load_raw(self):
        local_data = self._info["shapes"]["dict"]
        if "data" in local_data:
            return

        with open(self._info.get("path"), "r", encoding="utf-8") as f:
            raw = json.loads(f.read())
            local_data["data"] = raw