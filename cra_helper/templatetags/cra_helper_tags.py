"""
JSON filter courtesy of https://gist.github.com/pirate/c18bfe4fd96008ffa0aef25001a2e88f
"""

import json as jsonlib
import logging

import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def json(value):
    """
    Sanitize the JSON string using the Bleach HTML tag remover
    """
    uncleaned = jsonlib.dumps(value)
    clean = bleach.clean(uncleaned)
    return mark_safe(clean)
