import os, json

from compost.context import context
from datetime import datetime

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
        indent = len(n.split(".")) - 2
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


def section(section_name, subsection=""):
    current_major_section = context.recall("current_major_section", 0)
    new_major_section = current_major_section + 1
    context.remember("current_major_section", new_major_section)
    if subsection != "":
        subsection = "." + subsection
    section_number = str(new_major_section) + subsection

    toc = context.recall("toc", {})
    toc[section_number] = section_name
    context.remember("toc", toc)

    return '<a name="' + section_number + '"></a>' + section_number + " " + section_name


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