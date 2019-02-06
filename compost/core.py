import os, shutil, codecs, json, re
from jinja2 import Environment, select_autoescape, FileSystemLoader
from compost import models
from compost import utils
from compost import watcher
from compost.context import context

def build():
    _clean_directories()
    _load_data()
    _generate_stage()
    _copy_assets()
    _compile_templates()
    _render_sections()


def _clean_directories():
    config = context.config
    bd = config.build_dir()
    od = config.out_dir()
    if os.path.exists(bd):
        shutil.rmtree(bd)
    os.mkdir(bd)

    if os.path.exists(od):
        for the_file in os.listdir(od):
            file_path = os.path.join(od, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)
    else:
        os.mkdir(od)

    generate_dir = os.path.join(bd, "generate")
    if not os.path.exists(generate_dir):
        os.mkdir(generate_dir)

    post_template_dir = os.path.join(bd, "post_template")
    if not os.path.exists(post_template_dir):
        os.mkdir(post_template_dir)

def _load_data():
    config = context.config
    dd = os.path.join(config.src_dir(), "data")
    files = os.listdir(dd)
    data = models.Data(config)
    for file in files:
        data_file = os.path.join(dd, file)
        data.add_ref(data_file)
    context.data = data

def _generate_stage():
    """Not specified yet"""
    pass

def _copy_assets():
    config = context.config
    src_dir = config.src_dir()
    source = os.path.join(src_dir, "assets")
    od = config.out_dir()
    target = os.path.join(od, "assets")
    shutil.copytree(source, target)

def _compile_templates():
    config = context.config
    bd = config.build_dir()
    post_template_dir = os.path.join(bd, "post_template")
    src_dir = config.src_dir()
    content_path = os.path.join(src_dir, "content")
    templates_path = os.path.join(src_dir, "templates")
    env = Environment(
        loader=FileSystemLoader([content_path, templates_path]),
        autoescape=select_autoescape(['html'])
    )
    env.globals.update(
        config=context.config,
        data=context.data,
        url_for=utils.url_for
    )

    pages_path = os.path.join(content_path, "pages")
    pages = [f for f in os.listdir(pages_path) if os.path.isfile(os.path.join(pages_path, f))]

    for page in pages:
        template = env.get_template(os.path.join("pages", page))
        rendered = template.render()
        with codecs.open(os.path.join(post_template_dir, page), "wb", "utf-8") as f:
            f.write(rendered)

def _render_sections():
    config = context.config
    bd = config.build_dir()
    post_template_dir = os.path.join(bd, "post_template")
    pages = [f for f in os.listdir(post_template_dir) if os.path.isfile(os.path.join(post_template_dir, f))]

    for page in pages:
        suffix = page.rsplit(".", 1)[-1]
        main_renderer = config.renderer_for_file_suffix(suffix)
        with codecs.open(os.path.join(post_template_dir, page), "rb", "utf-8") as f:
            content = f.read()

        construct = _construct_from_text(content, main_renderer)
        text = construct.render()
        with codecs.open(os.path.join(config.out_dir(), page), "wb", "utf-8") as f:
            f.write(text)


def _construct_from_text(content, main_renderer):
    config = context.config
    construct = models.RenderConstruct(main_renderer)

    open_tag_rx = r"\{\[([^\]/\s]+)\]\}"

    tag_stack = []
    looking_for = "open"

    while len(content) > 0:
        bits = []
        if looking_for == "open":
            bits = re.split(open_tag_rx, content, 1)
        elif looking_for == "close":
            close_tag_rx = r"\{\[/" + tag_stack[-1] + r"\]\}"
            bits = re.split(close_tag_rx, content, 1)

        if len(bits) == 1:
            # there is no open or close tag until the end of the string
            construct.append(bits[0])
            content = ""

        elif len(bits) == 2:
            # we have encountered a close tag
            construct.append(bits[0])
            content = bits[1]
            construct.pop()
            del tag_stack[-1]

            if len(tag_stack) == 0:
                looking_for = "open"
                continue

            looking_for = __is_next_tag_open_or_close(tag_stack[-1], open_tag_rx, content)

        elif len(bits) == 3:
            # we have encountered an open tag
            construct.append(bits[0])
            r = config.renderer_for_inline_tag(bits[1])
            construct.push(r)
            content = bits[2]
            tag_stack.append(bits[1])

            looking_for = __is_next_tag_open_or_close(bits[1], open_tag_rx, content)

    return construct

def __is_next_tag_open_or_close(current_tag, open_tag_rx, content):
    close_tag_rx = r"\{\[/" + current_tag + r"\]\}"
    open_match = re.search(open_tag_rx, content)
    close_match = re.search(close_tag_rx, content)
    open_start = -1
    close_start = -1
    if open_match:
        open_start = open_match.start()
    if close_match:
        close_start = close_match.start()
    else:
        close_start = len(content)

    if open_start > -1 and open_start < close_start:
        return "open"
    else:
        return "close"

def build_closure():
    def build_callback(report):
        print report
        build()
    return build_callback

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", help="operational mode for compost: build, integrate, serve")
    parser.add_argument("config", help="config file for this run")
    args = parser.parse_args()

    baseDir = os.path.dirname(args.config)

    with codecs.open(args.config) as f:
        config = json.loads(f.read())

    config["base_dir"] = baseDir
    config = models.Config(config)
    context.config = config

    if args.mode == "build":
        build()
    elif args.mode == "integrate":
        watcher.watch(config.src_dir(), build_closure())
    else:
        print "Unrecognised mode"

if __name__ == "__main__":
    main()