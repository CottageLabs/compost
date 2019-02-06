no_tags = "this text has no nested tags"
one_level = "this text has {[md]}several{[/md]} tags in {[md]}series{[/md]}"
two_level = "this text has {[md]}multiple {[html]}nested{[/html]} layer of{[/md]} tags {[md]}inside {[md]}each{[/md]} other{[/md]}"

from compost import core, models
from compost.context import context
from compost.renderers.html import HTMLRenderer

context.config = models.Config()

construct = core._construct_from_text(no_tags, HTMLRenderer("html"))
# print(construct)
print(construct.render())

construct = core._construct_from_text(one_level, HTMLRenderer("html"))
# print(construct)
print(construct.render())

construct = core._construct_from_text(two_level, HTMLRenderer("html"))
# print(construct)
print(construct.render())