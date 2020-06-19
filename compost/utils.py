import os, json

from compost.context import context
from compost import exceptions
from datetime import datetime
import markdown


###############################################
## Template Functions/Filters
###############################################

def url_for(source_file, anchor=None):
    base = "/"
    settings = context.config.util_properties("url_for")
    if settings.get("include_base_url", True):
        base = context.config.base_url
    if not settings.get("include_file_suffix", True):
        source_file = source_file.rsplit(".", 1)[0]
    url = base + source_file
    if anchor is not None:
        url = "#" + anchor
    return url


def export_url(source_file, anchor=None):
    target = context.config.export_target(source_file)
    base = "/"
    settings = context.config.util_properties("export_url")
    if settings.get("include_base_url", True):
        base = context.config.base_url
    if not settings.get("include_file_suffix", True):
        target = target.rsplit(".", 1)[0]
    url = base + target
    if anchor is not None:
        url = "#" + anchor
    return url


def now(format):
    return datetime.utcnow().strftime(format)


def toc():
    toc = context.recall("toc")
    if toc is None:
        return "{{ toc() }}"

    numbers = list(toc.keys())
    numbers.sort(key=lambda s: [int(u) for u in s.split('.') if u.strip() != ""])
    frag = "{% markdown %}"
    for n in numbers:
        indent = len(n.split(".")) - 1
        frag += "\t" * indent + "* [" + n + ". " + toc[n] + "](#" + n + ")\n"
    frag += "{% endmarkdown %}"
    return frag


def ref(reference):
    """Insert a link to a reference in some unspecified references section"""
    def _anchor_name(v):
        v = v.lower().strip()
        return v.replace(" ", "_")

    records = context.data.get("references").shape("dict")
    for entry in records:
        if entry.get("ID") == reference:
            return "[[" + reference + "](#" + _anchor_name(reference) + ")]"


def header(name, level=1):
    current = context.recall("current_header", [0])
    idx = level - 1
    if len(current) < level:
        current += [0] * (level - len(current))
    current[idx] += 1
    for i in range(idx + 1, len(current)):
        current[i] = 0
    context.remember("current_header", current)

    number = ".".join([str(x) for x in current if x != 0])

    toc = context.recall("toc", {})
    toc[number] = name
    context.remember("toc", toc)

    return '<a name="' + number + '"></a>' + number + ". " + name


def json_schema_definitions(data_handle):
    schema_doc = context.data.get(data_handle).shape("dict")

    def _recurse_properties(rows, props, prefix):
        for prop, val in props.items():
            title = val.get("title", "")
            desc = val.get("description", "")
            text = ""
            if title != "":
                text = title
            if desc != "":
                if text != "":
                    text += "\n\n"
                text += desc
            field_name = prefix + prop
            rows.append([field_name, val.get("type"), text])

            if "properties" in val:
                _recurse_properties(rows, val.get("properties", {}), field_name + ".")
            elif "items" in val:
                if "properties" in val.get("items", {}):
                    _recurse_properties(rows, val.get("items", {}).get("properties", {}), field_name + "[].")

    rows = []
    _recurse_properties(rows, schema_doc.get("properties", {}), "")
    _recurse_properties(rows, schema_doc.get("patternProperties", {}), "")

    rows.sort(key=lambda x: x[0])
    frag =  "| Field | Type | Description |\n"
    frag += "| ----- | ---- | ----------- |\n"
    for row in rows:
        desc = row[2]
        desc = desc.replace("\n", "<br>")
        frag += "| " + row[0] + " | " + row[1] + " | " + desc + " |\n"
    return "{% markdown %}" + frag + "{% endmarkdown %}"


def section_link(header):
    toc = context.recall("toc")
    for k, v in toc.items():
        if v == header:
            return "[" + header + "](#" + k + ")"
    return "{{ section_link('{x}') }}".format(x=header)
    # raise exceptions.InconsistentStructureException("Unable to find header " + header)


def sections(source, header_field, header_level, order, list_fields, intro):
    if not isinstance(order, list):
        order = [order]
    if not isinstance(list_fields, list):
        list_fields = [list_fields]
    if not isinstance(intro, list):
        intro = [intro]
    header_level = int(header_level)

    intros = {}
    for pair in intro:
        bits = pair.split(":")
        intros[bits[0]] = bits[1]

    rows = context.data.get(source).shape("table")
    headers = rows.next()

    hindex = 0
    for i in range(len(headers)):
        h = headers[i]
        if header_field == h:
            hindex = i

    oindex = []
    for o in order:
        for i in range(len(headers)):
            if o == headers[i]:
                oindex.append(i)
                break

    frag = ""
    for row in rows:
        frag += "#" * header_level + " " + row[hindex] + "\n\n"
        for o in oindex:
            content = row[o]
            if content == "":
                continue
            if headers[o] in intros:
                frag += intros[headers[o]] + "\n\n"
            if headers[o] in list_fields:
                thelist = ""
                bits = [c.strip() for c in content.split(",")]
                for b in bits:
                    thelist += " * " + b + "\n"
                content = thelist
            frag += content + "\n\n"

    return frag


def dl(source, term, definition, link=None, size=None, offset=0, filter_field=None, filters=None):
    def _anchor_name(v):
        v = v.lower().strip()
        return v.replace(" ", "_")

    rows = context.data.get(source).shape("table")
    frag = "<dl>"
    offset = int(offset)
    if size is not None:
        size = int(size)
    if filters is not None:
        if not isinstance(filters, list):
            filters = [filters]

    headers = rows.next()

    filter_idx = -1
    if filter_field is not None:
        for i in range(len(headers)):
            if headers[i] == filter_field:
                filter_idx = i

    n = 0
    for row in rows:
        if filter_field is not None:
            val = row[filter_idx]
            if val not in filters:
                continue

        if size is not None and n >= size + offset:
            break
        n += 1
        if n < offset + 1:
            continue

        dt = None
        dd = None
        a = ""
        for i in range(len(row)):
            col = row[i]
            name = headers[i]
            if name == term:
                a = '<a name="' + _anchor_name(col) + '"></a>'
            if name == link:
                col = "[" + col + "](" + col + ")"
            if name == term:
                dt = col
                continue
            if name == definition:
                dd = col
                continue
        dt = markdown.markdown(dt)[3:-4]    # removes the <p> and </p> markdown inserts
        dd = markdown.markdown(dd)[3:-4]    # removes the <p> and </p> markdown inserts
        frag += "<dt>" + a + dt + "</dt><dd>" + dd + "</dd>"

    frag += "</dl>"
    return frag


def table(source):
    rows = context.data.get(source).shape("table")
    headers = rows.next()
    frag = "| " + " | ".join(headers) + " |\n"
    frag += "| " + "--- |" * len(headers) + "\n"
    for row in rows:
        linified_row = [cell.replace("\n", "<br>") for cell in row]
        frag += "| " + " | ".join(linified_row) + " |\n"
    return frag


###############################################


def rel2abs(file, *args):
    file = os.path.realpath(file)
    if os.path.isfile(file):
        file = os.path.dirname(file)
    return os.path.abspath(os.path.join(file, *args))


def merge_dicts(target, source):
    for k, v in source.items():
        if k in target:
            if isinstance(target[k], dict):
                if isinstance(source[k], dict):
                    merge_dicts(target[k], source[k])
                else:
                    target[k] = source[k]
            elif isinstance(target[k], list) or isinstance(target[k], set):
                if isinstance(source[k], list) or isinstance(source[k], set):
                    target[k] = source[k]
            else:
                if not (isinstance(source[k], dict) or isinstance(source[k], list) or isinstance(source[k], set)):
                    target[k] = source[k]
        else:
            target[k] = source[k]
    return target

class RendererJSONEncoder(json.JSONEncoder):
    def default(self, o):
        from compost.models import Renderer
        if isinstance(o, Renderer):
            return o.__name__
        return o