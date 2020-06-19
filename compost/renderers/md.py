# -*- coding: utf-8 -*-

import markdown

from compost.models import Renderer
from compost.context import context

from jinja2.nodes import CallBlock
from jinja2.ext import Extension


class MarkdownExtension(Extension):
    tags = {'markdown'}

    def __init__(self, environment):
        super(MarkdownExtension, self).__init__(environment)
        self._settings = None
        # self._settings = environment.globals.config.settings_for_tag("markdown")
        #environment.extend(
        #    markdowner=markdown.Markdown(extensions=['extra'])
        #)

    def parse(self, parser):
        if self._settings is None:
            self._settings = self.environment.globals.get("config").settings_for_tag("markdown")
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(
            ['name:endmarkdown'],
            drop_needle=True
        )
        return CallBlock(
            self.call_method('_markdown_support'),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _markdown_support(self, caller):
        block = caller()
        block = self._strip_whitespace(block)
        return self._render_markdown(block)

    def _strip_whitespace(self, block):
        lines = block.split('\n')
        whitespace = ''
        output = ''

        if (len(lines) > 1):
            for char in lines[1]:
                if (char == ' ' or char == '\t'):
                    whitespace += char
                else:
                    break

        for line in lines:
            output += line.replace(whitespace, '', 1) + '\r\n'

        return output.strip()

    def _render_markdown(self, block):
        body = markdown.markdown(block, extensions=self._settings.get("settings", {}).get("extensions", []))
        return body


"""
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
"""