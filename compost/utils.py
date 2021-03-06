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
        base = context.config.base_url()
    if not settings.get("include_file_suffix", True):
        source_file = source_file.rsplit(".", 1)[0]
    url = base + source_file
    if anchor is not None:
        url = url + "#" + anchor
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


def toc(id="main"):
    tocs = context.recall("tocs", {})
    toc = tocs.get(id)

    # toc = context.recall("toc")
    if toc is None:
        return '{% autoescape off %}{{ toc("' + id + '") }}{% endautoescape %}'

    numbers = list(toc.keys())
    numbers.sort(key=lambda s: [int(u) for u in s.split('.') if u.strip() != ""])
    frag = "{% markdown %}\n"
    for n in numbers:
        indent = len(n.split(".")) - 1
        frag += "\t" * indent + "* [" + n + ". " + toc[n] + "](#" + n + ")\n"
    frag += "{% endmarkdown %}"
    return frag


@is_inline_markdown
def ref(reference):
    """Insert a link to a reference in some unspecified references section"""
    settings = context.config.util_properties("ref")
    records = context.data.get(settings.get("source", "references")).shape("dict")
    for entry in records:
        if entry.get("ID") == reference:
            return "[[" + reference + "](#" + _anchor_name(reference) + ")]"


def header(name, level=1, toc="main"):
    registry = context.recall("header_registry", {})
    current = registry.get(toc, [0])
    # current = context.recall("current_header", [0])
    idx = level - 1
    if len(current) < level:
        current += [0] * (level - len(current))
    current[idx] += 1
    for i in range(idx + 1, len(current)):
        current[i] = 0

    registry[toc] = current
    context.remember("header_registry", registry)

    number = ".".join([str(x) for x in current if x != 0])

    tocs = context.recall("tocs", {})
    tocinst = tocs.get(toc, {})
    tocinst[number] = name
    tocs[toc] = tocinst
    context.remember("tocs", tocs)

    #toc = context.recall("toc", {})
    #toc[number] = name
    #context.remember("toc", toc)

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
def section_link(header, toc="main"):
    tocs = context.recall("tocs", {})
    tocinst = tocs.get(toc, {})

    # toc = context.recall("toc")
    for k, v in tocinst.items():
        if v == header:
            return "[" + header + "](#" + k + ")"
    return '{% autoescape off %}{{ section_link("' + header + '", "' + toc + '") }}{% endautoescape %}'
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
def table(source, anchor=None, anchor_prefix=""):
    rows = context.data.get(source).shape("table")
    headers = rows.next()
    frag = "| " + " | ".join(headers) + " |\n"
    frag += "| " + "--- |" * len(headers) + "\n"
    for row in rows:
        linified_row = [cell.replace("\n", "<br>") for cell in row]
        if anchor is not None:
            v = linified_row[anchor]
            linified_row[anchor] = '<a name="' + anchor_prefix + _anchor_name(v) + '">' + v + '</a>'
        frag += "| " + " | ".join(linified_row) + " |\n"
    return frag


def json_extract(source, keys=None, exclude=None, selector=None, listobj_match=None, unwrap_single_entry_list=False, insert=None):
    if keys is not None and not isinstance(keys, list):
        keys = [keys]
    include = keys

    if exclude is not None and not isinstance(exclude, list):
        exclude = [exclude]

    if insert is None:
        insert = {}

    bd = context.config.src_dir()
    path = os.path.join(bd, source)
    with open(path, "r", encoding="utf-8") as f:
        js = json.loads(f.read())

    if selector is not None:
        js = js[selector]

    show = {}
    if include is None:
        show = js
    else:
        for key in include:
            if key in js:
                show[key] = js[key]

    if exclude is not None:
        for key in exclude:
            if key in show:
                del show[key]

    if listobj_match is not None:
        keep = []
        for obj in show:
            for k, v in listobj_match.items():
                if obj.get(k) == v:
                    keep.append(obj)
        show = keep

    if isinstance(show, list) and len(show) == 1 and unwrap_single_entry_list:
        show = show[0]

    show.update(insert)

    out = json.dumps(show, indent=2, sort_keys=True)
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


def requirements_hierarchy(source, key):
    rows = context.data.get(source).shape("table")
    filtered = []
    for row in rows:
        if row[0] == key:
            filtered.append(row[1:])

    h = {}
    c = h
    for row in filtered:
        for cell in row:
            if cell == "":
                break
            if cell not in c:
                c[cell] = {}
            c = c[cell]
        c = h

    def _recurse_heirarchy(node, depth):
        frag = ""
        for k, v in node.items():
            if k == "*":
                k = "All"
            frag += "\t" * (depth - 1) + "* " + k.replace("*", "\*") + "\n"
            if len(v.keys()) != 0:
                frag += _recurse_heirarchy(v, depth + 1)
        return frag

    frag = _recurse_heirarchy(h, 1)
    return frag


@is_markdown
def requirements_table_2(source, vectors, reqs, definitions=None):
    if not isinstance(vectors, list):
        vectors = [vectors]
    if not isinstance(reqs, list):
        reqs = [reqs]

    defs = {}
    if definitions is not None:
        reader = context.data.get(definitions).shape("table")
        headers = reader.next()
        defs = {headers[0] : {}}
        for row in reader:
            defs[headers[0]][row[0]] = row[1].replace("*", "\*")

    reader = context.data.get(source).shape("table")
    headers = reader.next()

    idx = {}
    for i in range(len(headers)):
        h = headers[i]
        for v in vectors:
            if h == v:
                idx[v] = i
                break
        for r in reqs:
            if h == r:
                idx[r] = i
                break

    vector_sections = []
    expanded_requirements = {}
    for row in reader:
        vector_section = []
        for v in vectors:
            vector_section.append(row[idx[v]])
        if not vector_section in vector_sections:
            vector_sections.append(vector_section)
        id = vector_sections.index(vector_section)
        if id not in expanded_requirements:
            expanded_requirements[id] = {}
        for r in reqs:
            if r not in expanded_requirements[id]:
                expanded_requirements[id][r] = []
            val = row[idx[r]]
            if val != "" and val not in expanded_requirements[id][r]:
                expanded_requirements[id][r].append(val)

    frag = ""
    for i in range(len(vector_sections)):
        vs = vector_sections[i]
        ctx = expanded_requirements[i]

        frag += "**Request Conditions**:\n\n"
        for j in range(len(vs)):
            vname = vs[j]
            vtype = vectors[j]
            if vname == "*":
                vname = "All"
            frag += "* **" + vtype + "**: " + vname + "\n"
        frag += "\n"

        for r in reqs:
            vals = ctx[r]
            if len(vals) == 0:
                continue
            cell = ""
            for v in vals:
                deftext = ""
                if r in defs:
                    deftext = " - " + defs[r][v]
                cell += "* " + v + deftext + "\n"

            frag += "**" + r + "**\n\n"
            frag += cell + "\n"

        frag += "<hr>"

    return frag


def content_disposition(reqs, hierarchy, groups, match):
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


def openapi_list_descriptions(source, field, keys,
                              expand_source=None, expand_on=None, expand_field=None, expand_prefix="", expand_suffix="",
                              expand_anchor=False, expand_anchor_prefix=""):
    expand = None
    if expand_source is not None:
        expand = context.data.get(expand_source).shape("dict")

    api = context.data.get(source).shape("dict")
    bits = field.split(".")
    for bit in bits:
        api = api.get(bit)

    frag = ""

    if not isinstance(keys, list):
        keys = [keys]
    for key in keys:
        desc = api.get(key).get("description")

        additional = []
        if expand is not None:
            expand.reset()
            for e in expand:
                if e.get(expand_on) == key:
                    v = e.get(expand_field)
                    if expand_anchor:
                        ank = expand_anchor_prefix + _anchor_name(v)
                        v = '<a href="#' + ank + '">' + v + '</a>'
                    additional.append(v)
            if len(additional) > 0:
                desc += expand_prefix + ", ".join(additional) + expand_suffix

        frag += " * " + desc + "\n"

    return frag


def openapi_paths(source, path_order=None, method_order=None, header_depth=1, omit=None, in_brief=None):
    if method_order is None:
        method_order = ["get", "post", "put", "delete"]
    header_depth = int(header_depth)

    api = context.data.get(source).shape("dict")

    paths = api.get("paths")
    path_names = paths.keys()
    if path_order is not None:
        path_names = ["/" + po for po in path_order]
    frag = ""
    for pn in path_names:
        path_info = paths.get(pn)
        if path_info is None:
            continue
        for method in method_order:
            method_info = path_info.get(method)
            if method_info is None:
                continue
            frag += _render_method_info(header_depth, pn, method, method_info, omit, in_brief)

    return frag


def _render_method_info(header_depth, path_name, method, method_info, omit=None, in_brief=None):
    htext = header(method.upper() + " " + path_name[1:], header_depth)
    frag = "#" * header_depth + htext + "\n\n"
    frag += '<div class="openapi">{% markdown %}'
    frag += method_info.get("summary", "") + "\n\n"
    frag += "**Headers**\n\n"

    for param in method_info.get("parameters", []):
        if param.get("in") != "header":
            continue
        frag += " * " + param.get("name") + "\n"
    frag += "\n"

    rb = method_info.get("requestBody")
    if rb is not None:
        frag += "**Body**\n\n"
        frag += rb.get("description", "") + "\n\n"

    frag += "**Responses**\n\n"

    frag += "| Code | Description |\n"
    frag += "| ---- | ----------- |\n"
    codes = method_info.get("responses", [])
    keys = codes.keys()
    keys = sorted(keys)
    for code in keys:
        if code in omit:
            continue
        if code in in_brief:
            code_info = codes.get(code)
            frag += "| " + code + " | " + code_info.get("description", "") + " |\n"
        else:
            code_info = codes.get(code)
            frag += "| " + code + " | " + code_info.get("description", "") + "<br><br>"

            headers = code_info.get("headers", [])
            if len(headers) > 0:
                frag += "**Headers**"
                frag += "<ul>"
                for h, hobj in headers.items():
                    frag += "<li>" + h + " - " + hobj.get("description") + "</li>"
                frag += "</ul>"

            frag += "**Body**<ul>"
            content = code_info.get("content", [])
            if len(content) > 0:
                for ct, cobj in content.items():
                    ct = ct.replace("*", "\*")
                    frag += "<li>" + ct + "</li>"
            else:
                frag += "<li>None</li>"
            frag += "</ul> |\n"

    frag += "{% endmarkdown %}</div>"
    return frag + "\n\n"


@is_markdown
def table_rows_as_paras(source, links=None, bold=None, anchor=None):
    reader = context.data.get(source).shape("table")
    paras = []
    headers = reader.next()

    for row in reader:
        para = ""
        for i in range(len(row)):
            col = row[i]
            name = headers[i]

            a = ""
            if name == anchor and anchor is not None:
                a = '<a name="' + _anchor_name(col) + '">'

            if name == links and links is not None:
                col = "[" + col + "](" + col + ")"
            if name == bold and bold is not None:
                col = "**" + col + "**"

            para += a + col + " "
        paras.append(para)

    return "\n\n".join(paras)


@is_inline_markdown
def anchor_link(error):
    settings = context.config.util_properties("anchor_link")
    prefix = settings.get("anchor_prefix")
    target = settings.get("target_document")
    ank = prefix + _anchor_name(error)
    url = url_for(target, ank)
    return "[" + error + "](" + url + ")"


@is_markdown
def http_exchange(source, method, url, response, include_headers=None, request_body=None, request_headers=None, response_headers=None):
    if include_headers is not None:
        if not isinstance(include_headers, list):
            include_headers = [include_headers]
    else:
        include_headers = []

    response = str(response)

    if request_headers is None:
        request_headers = {}

    if response_headers is None:
        response_headers = {}

    frag = method.upper() + " " + url + " HTTP/1.1\n"
    api = context.data.get(source).shape("dict")
    paths = api.get("paths")
    path = paths.get(url)
    request = path.get(method)

    headers = [p for p in request.get("parameters", []) if p.get("in") == "header"]
    if include_headers is not None:
        headers = [h for h in headers if h.get("name") in include_headers]
    for h in headers:
        val = request_headers.get(h.get("name"), "...")
        frag += h.get("name") + ": " + val + "\n"

    if request_body is None:
        request_body = request.get("requestBody", {}).get("description")
    if request_body is not None:
        frag += "\n"
        frag += "[" + request_body + "]\n"

    frag += "\n-----\n"

    frag += "HTTP/1.1 " + str(response) + "\n"
    resp = request.get("responses", {}).get(response, {})
    resp_headers = resp.get("headers", {}).keys()
    resp_headers = [h for h in resp_headers if h in include_headers]
    for rh in resp_headers:
        val = response_headers.get(rh, "...")
        frag += rh + ": " + val + "\n"
    cts = list(resp.get("content", {}).keys())
    if len(cts) > 0:
        frag += "Content-Type: " + cts[0] + "\n"
    frag += "\n"
    frag += "[" + resp.get("description", "Empty Body") + "]\n"

    return frag


def img(target, alt=None):
    base = context.config.base_url()
    altText = ""
    if alt is not None:
        altText = alt
    frag = '<div><img src="' + base + target + '" alt="' + altText + '"></div>'
    return frag


def fig(target, alt=None):
    frag = img(target, alt)
    if alt is not None:
        figs = context.recall("figures", [])
        altText = "Figure " + str(len(figs) + 1) + ": " + alt
        frag += '<div class="figure_label">' + altText + '</div>'
        figs.append(alt)
        context.remember("figures", figs)

    return frag


def ul(source, field, link=None, size=None, offset=0, filter_field=None, filters=None):

    frag = "<ul>"
    offset = int(offset)
    if size is not None:
        size = int(size)
    if filters is not None:
        if not isinstance(filters, list):
            filters = [filters]

    reader = context.data.get(source).shape("table")
    headers = reader.next()

    filter_idx = -1
    if filter_field is not None:
        for i in range(len(headers)):
            if headers[i] == filter_field:
                filter_idx = i

    n = 0
    for row in reader:
        if filter_field is not None:
            val = row[filter_idx]
            if val not in filters:
                continue

        if size is not None and n >= size + offset:
            break
        n += 1
        if n < offset + 1:
            continue

        li = None
        a = ""
        for i in range(len(row)):
            col = row[i]
            name = headers[i]
            if name == field:
                a = '<a name="' + _anchor_name(col) + '"></a>'
            if name == link:
                col = "[" + col + "](" + col + ")"
            if name == field:
                li = col
                continue
        li = markdown.markdown(li)[3:-4]    # removes the <p> and </p> markdown inserts
        frag += "<li>" + a + li + "</li>"

    frag += "</ul>"
    return frag

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