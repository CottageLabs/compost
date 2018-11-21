import os, shutil, codecs, json
from jinja2 import Environment, select_autoescape, FileSystemLoader
import models

def run(config):
    _clean_directories(config)
    _generate_stage(config)
    _copy_assets(config)
    _compile_templates(config)


def _clean_directories(config):
    bd = config.build_dir()
    od = config.out_dir()
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
    src_dir = config.src_dir()
    source = os.path.join(src_dir, "assets")
    od = config.out_dir()
    target = os.path.join(od, "assets")
    shutil.copytree(source, target)

def _compile_templates(config):
    src_dir = config.src_dir()
    pages_path = os.path.join(src_dir, "content", "pages")
    templates_path = os.path.join(src_dir, "templates")
    env = Environment(
        loader=FileSystemLoader([pages_path, templates_path]),
        autoescape=select_autoescape(['html'])
    )

    pages = [f for f in os.listdir(pages_path) if os.path.isfile(os.path.join(pages_path, f))]

    for page in pages:
        template = env.get_template(page)
        rendered = template.render()
        with codecs.open(os.path.join(config.out_dir(), page), "wb", "utf-8") as f:
            f.write(rendered)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="config file for build")
    args = parser.parse_args()

    baseDir = os.path.dirname(args.config)

    with codecs.open(args.config) as f:
        config = json.loads(f.read())

    config["base_dir"] = baseDir
    config = models.Config(config)
    run(config)

if __name__ == "__main__":
    main()