import os, shutil, codecs
from jinja2 import Environment, select_autoescape, FileSystemLoader

def run(config):
    _clean_directories(config)
    _generate_stage(config)
    _copy_assets(config)
    # _unprocessed_sources(config)
    # _expand_stage(config)
    _compile_templates(config)


def _clean_directories(config):
    bd = config.get("build_dir")
    od = config.get("out_dir")
    if os.path.exists(bd):
        shutil.rmtree(bd)
    if os.path.exists(od):
        shutil.rmtree(od)
    os.mkdir(bd)
    os.mkdir(od)

    generate_dir = os.path.join(bd, "generate")
    """
    expand_dir = os.path.join(bd, "expand")
    number_dir = os.path.join(bd, "number")
    index_dir = os.path.join(bd, "index")
    integrate_dir = os.path.join(bd, "integrate")
    if not os.path.exists(expand_dir):
        os.mkdir(expand_dir)
    if not os.path.exists(number_dir):
        os.mkdir(number_dir)
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    if not os.path.exists(integrate_dir):
        os.mkdir(integrate_dir)
    """
    if not os.path.exists(generate_dir):
        os.mkdir(generate_dir)

def _generate_stage(config):
    """Not specified yet"""
    pass

def _copy_assets(config):
    src_dir = config.get("src_dir")
    source = os.path.join(src_dir, "assets")
    od = config.get("out_dir")
    target = os.path.join(od, "assets")
    shutil.copytree(source, target)

def _compile_templates(config):
    pages_path = os.path.join(config["src_dir"], "content", "pages")
    templates_path = os.path.join(config["src_dir"], "templates")
    env = Environment(
        loader=FileSystemLoader([pages_path, templates_path]),
        autoescape=select_autoescape(['html'])
    )

    pages = [f for f in os.listdir(pages_path) if os.path.isfile(os.path.join(pages_path, f))]

    for page in pages:
        template = env.get_template(page)
        rendered = template.render()
        with codecs.open(os.path.join(config["out_dir"], page), "wb", "utf-8") as f:
            f.write(rendered)

run({
    "src_dir" : "example/source",
    "out_dir" : "example/output",
    "build_dir" : "example/build"
})