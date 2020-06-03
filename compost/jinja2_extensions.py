from jinja2 import BaseLoader

class MarkupWrapperLoader(BaseLoader):
    def __init__(self, inner, config):
        self.inner = inner
        self.config = config

    def get_source(self, environment, template):
        contents, filename, uptodate = self.inner.get_source(environment, template)
        bits = filename.split(".")
        if len(bits) > 1:
            suffix = bits[-1]
            settings = self.config.settings_for_file_suffix(suffix)
            if settings is not None:
                tag = settings.get("jinja2_tag")
                contents = "{% " + tag + " %}" + contents + "{% end" + tag + " %}"
        return contents, filename, uptodate

    def list_templates(self):
        return self.inner.list_templates()