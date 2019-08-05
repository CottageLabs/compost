def default_dict_filter(filter_settings):

    def default_dict_filter_impl(record):
        match_count = 0
        for key, val in filter_settings.items():
            rval = record.get(key)
            if rval == val:
                match_count += 1
        return match_count == len(filter_settings)

    return default_dict_filter_impl


def default_dict_sort(sort_settings):
    key = [*sort_settings][0]
    dir = sort_settings[key]
    reverse = dir == "desc"

    def default_dict_sort_impl(val):
        sv = val[key]
        try:
            return float(sv)
        except:
            if sv == "":
                return 0
            return sv

    return default_dict_sort_impl, reverse