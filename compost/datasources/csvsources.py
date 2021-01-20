import codecs
from compost import models, utf8csv

class TableCSVDataSource(models.TableDataSource):
    def __init__(self, info, config):
        super(TableCSVDataSource, self).__init__(info, config)
        if "shapes" not in self._info:
            self._info["shapes"] = {}
        self._info["shapes"]["table"] = {}

    def __iter__(self):
        self._load_raw()
        local_data = self._info["shapes"]["table"]
        if "idx" not in local_data:
            local_data["idx"] = 0
        return self

    def __next__(self):
        return self.next()

    def reset(self):
        local_data = self._info["shapes"]["table"]
        local_data["idx"] = 0

    def next(self):
        self._load_raw()
        local_data = self._info["shapes"]["table"]
        if "idx" not in local_data:
            local_data["idx"] = 0
        idx = local_data["idx"]
        if len(local_data["data"]) > idx:
            record = local_data["data"][idx]
            local_data["idx"] = idx + 1
            return record
        else:
            local_data["idx"] = 0
            raise StopIteration()

    def _load_raw(self):
        local_data = self._info["shapes"]["table"]
        if "data" in local_data:
            return

        with open(self._info.get("path"), "r", encoding="utf-8") as f:
            reader = utf8csv.UnicodeReader(f)
            local_data["data"] = []
            for row in reader:
                local_data["data"].append(row)
        return


class DictCSVDataSource(models.DictDataSource):
    def __init__(self, info, config):
        super(DictCSVDataSource, self).__init__(info, config)
        if "shapes" not in self._info:
            self._info["shapes"] = {}
        self._info["shapes"]["dict"] = {}

    def __iter__(self):
        self._prep_iterator()
        return self

    def __next__(self):
        return self.next()

    def reset(self):
        local_data = self._info["shapes"]["dict"]
        local_data["idx"] = 0

    def next(self):
        self._prep_iterator()
        local_data = self._info["shapes"]["dict"]

        def get_next_record():
            idx = local_data["idx"]
            local_data["idx"] = idx + 1
            if len(local_data["data"]) > idx:
                record = local_data["data"][idx]
                if not self.include_record(record):
                    return False
                return record
            else:
                raise StopIteration()

        while True:
            rec = get_next_record()
            if rec != False:
                return rec

    def _prep_iterator(self):
        local_data = self._info["shapes"]["dict"]
        if "data" in local_data:
            return

        local_data["idx"] = 0
        with codecs.open(self._info.get("path"), "rb", "utf-8") as f:
            reader = utf8csv.UnicodeReader(f)
            headers = reader.next()
            local_data["data"] = []
            for row in reader:
                obj = {}
                for i in range(len(headers)):
                    obj[headers[i]] = row[i]
                local_data["data"].append(obj)

        if self._sort is not None:
            local_data["data"].sort(key=self._sort_fn_dir[0], reverse=self._sort_fn_dir[1])