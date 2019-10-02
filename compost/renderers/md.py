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

class MarkdownInlineRenderer(MarkdownRenderer):
    def __init__(self, cfg_id):
        super(MarkdownInlineRenderer, self).__init__(cfg_id)

    def render(self, text):
        body = super(MarkdownInlineRenderer, self).render(text)
        if body.startswith("<p>"):
            body = body[3:]
        if body.endswith("</p>"):
            body = body[:-4]
        return body