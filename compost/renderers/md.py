import markdown
from compost.models import Renderer
from compost.context import context

class MarkdownRenderer(Renderer):
    def __init__(self, cfg_id):
        super(MarkdownRenderer, self).__init__(cfg_id)
        self._settings = context.config.renderer_settings(cfg_id)

    def render(self, text):
        body = markdown.markdown(text, extensions=self._settings.get("extensions", []))
        return body