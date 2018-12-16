def url_for(source_file, anchor=None):
    base = "/"
    url = base + source_file
    if anchor is not None:
        url = "#" + anchor
    return url