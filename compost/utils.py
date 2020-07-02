import os, json

from compost.context import context
from compost import exceptions
from datetime import datetime
import markdown


def is_markdown(func):
    def wrapper(*args, **kwargs):
        body = func(*args, **kwargs)
        return "{% markdown %}" + body + "{% endmarkdown %}"
    return wrapper


def is_inline_markdown(func):
    def wrapper(*args, **kwargs):
        body = func(*args, **kwargs)
        return "{% mdinline %}" + body + "{% endmdinline %}"
    return wrapper

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

@is_markdown
def ref(reference):
    """Insert a link to a reference in some unspecified references section"""
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

@is_markdown
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
    return frag


@is_inline_markdown
def section_link(header):
    toc = context.recall("toc")
    for k, v in toc.items():
        if v == header:
            return "[" + header + "](#" + k + ")"
    return '{% autoescape off %}{{ section_link("' + header + '") }}{% endautoescape %}'
    # raise exceptions.InconsistentStructureException("Unable to find header " + header)


@is_markdown
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


@is_markdown
def table(source):
    rows = context.data.get(source).shape("table")
    headers = rows.next()
    frag = "| " + " | ".join(headers) + " |\n"
    frag += "| " + "--- |" * len(headers) + "\n"
    for row in rows:
        linified_row = [cell.replace("\n", "<br>") for cell in row]
        frag += "| " + " | ".join(linified_row) + " |\n"
    return frag


def json_extract(source, keys=None, selector=None):
    if keys is not None and not isinstance(keys, list):
        keys = [keys]

    bd = context.config.src_dir()
    path = os.path.join(bd, source)
    with open(path, "r", encoding="utf-8") as f:
        js = json.loads(f.read())

    if selector is not None:
        js = js[selector]

    show = {}
    if keys is None:
        show = js
    else:
        for key in keys:
            if key in js:
                show[key] = js[key]

    out = json.dumps(show, indent=2)
    return out


def define(source, id):
    rows = context.data.get(source).shape("table")
    headers = rows.next()
    for row in rows:
        if row[0] == id:
            return id + '<sup>[<a href="#' + _anchor_name(id) + '">def</a>]</sup>'
    raise exceptions.InconsistentStructureException("Unable to find definition for " + id)


@is_markdown
def requirements(reqs, hierarchy, groups, match, output):
    """
    reqs=tables/requirements2.csv,
    hierarchy=tables/reqs_hierarchy.csv,
    groups=Request|Content|Resource,
    match=Retrieve|Empty Body|Service-URL,
    output=Protocol Operation|Request Requirements|Server Requirements|Response Requirements
    """
    if not isinstance(groups, list):
        groups = [groups]
    if not isinstance(match, list):
        match = [match]
    if not isinstance(output, list):
        output = [output]

    """
    bd = config.get("src_dir")
    reqs_path = os.path.join(bd, reqs)
    hierarchy_path = os.path.join(bd, hierarchy)

    headers = []
    requirements = []
    with codecs.open(reqs_path, "rb", "utf-8") as f:
        reqs_reader = UnicodeReader(f)
        headers = reqs_reader.next()
        for row in reqs_reader:
            requirements.append(row)

    hei = []
    with codecs.open(hierarchy_path, "rb", "utf-8") as f:
        hierarchy_reader = UnicodeReader(f)
        for row in hierarchy_reader:
            hei.append(row)
    """

    requirements = context.data.get(reqs).shape("table")
    hei = context.data.get(hierarchy).shape("table")
    headers = requirements.next()

    lookup = {}
    for i in range(len(groups)):
        group = groups[i]
        m = match[i]
        match_row = None
        for row in hei:
            broke = False
            if row[0] == group:
                for j in range(len(row) - 1, -1, -1):
                    if row[j] == m:
                        match_row = row
                        broke = True
                        break
                if broke:
                    break

        if match_row is not None:
            lookups = []
            for i in range(len(match_row)):
                if i == 0:
                    continue
                cell = match_row[i]
                if cell != "":
                    lookups.append(cell)

            lookup[group] = lookups

    idx = {}
    for i in range(len(headers)):
        h = headers[i]
        for group in groups:
            if h == group:
                idx[group] = i
                break
        for o in output:
            if "+" in o:
                o = o.split("+")
            if not isinstance(o, list):
                o = [o]
            for bit in o:
                if h == bit:
                    idx[bit] = i
                    break

    rs = []
    for r in requirements:
        score = 0
        for group in groups:
            if r[idx[group]] in lookup[group]:
                score += 1
        if score != len(groups):
            continue
        result = []
        for o in output:
            if "+" in o:
                o = o.split("+")
                text = ""
                for bit in o:
                    text += bit + " - "
                result.append(text)
            else:
                result.append(r[idx[o]])
        rs.append(result)

    sections = {}
    for r in rs:
        for i in range(len(output)):
            o = output[i]
            if o not in sections:
                sections[o] = []
            v = r[i]
            if v != "":
                sections[o].append(v)

    frag = ""
    for key in output:
        reqs = sections[key]
        if len(reqs) == 0:
            continue
        frag += "**" + key + "**\n\n"
        for req in reqs:
            frag += " * " + req.replace("\n", "<br>") + "\n"
        frag += "\n"
    return frag


def content_disposition(reqs, hierarchy, groups, match):
    """
    bd = config.get("src_dir")
    reqs_path = os.path.join(bd, reqs)
    hierarchy_path = os.path.join(bd, hierarchy)

    headers = []
    requirements = []
    with codecs.open(reqs_path, "rb", "utf-8") as f:
        reqs_reader = UnicodeReader(f)
        headers = reqs_reader.next()
        for row in reqs_reader:
            requirements.append(row)

    hei = []
    with codecs.open(hierarchy_path, "rb", "utf-8") as f:
        hierarchy_reader = UnicodeReader(f)
        for row in hierarchy_reader:
            hei.append(row)
    """

    requirements = context.data.get(reqs).shape("table")
    hei = context.data.get(hierarchy).shape("table")
    headers = requirements.next()

    lookup = {}
    for i in range(len(groups)):
        group = groups[i]
        m = match[i]
        match_row = None
        hei.reset()
        for row in hei:
            broke = False
            if row[0] == group:
                for j in range(len(row) - 1, -1, -1):
                    if row[j] == m:
                        match_row = row
                        broke = True
                        break
                if broke:
                    break

        if match_row is not None:
            lookups = []
            for i in range(len(match_row)):
                if i == 0:
                    continue
                cell = match_row[i]
                if cell != "":
                    lookups.append(cell)

            lookup[group] = lookups

    output = ["Disposition Type", "Param"]
    idx = {}
    for i in range(len(headers)):
        h = headers[i]
        for group in groups:
            if h == group:
                idx[group] = i
                break
        for o in output:
            if "+" in o:
                o = o.split("+")
            if not isinstance(o, list):
                o = [o]
            for bit in o:
                if h == bit:
                    idx[bit] = i
                    break

    rs = []
    for r in requirements:
        score = 0
        for group in groups:
            if r[idx[group]] in lookup[group]:
                score += 1
        if score != len(groups):
            continue
        result = []
        for o in output:
            if "+" in o:
                o = o.split("+")
                text = ""
                for bit in o:
                    text += bit + " - "
                result.append(text)
            else:
                result.append(r[idx[o]])
        rs.append(result)

    sections = {}
    for r in rs:
        for i in range(len(output)):
            o = output[i]
            if o not in sections:
                sections[o] = []
            v = r[i]
            if v != "":
                sections[o].append(v)

    parts = [sections["Disposition Type"][0]] + sections["Param"]
    return "Content-Disposition: " + "; ".join(parts)


###############################################
# shared (internal) utilities

def _anchor_name(v):
    v = v.lower().strip()
    return v.replace(" ", "_")


##############################################

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