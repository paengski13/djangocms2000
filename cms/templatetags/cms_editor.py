from django.contrib.auth.forms import AuthenticationForm
from django.template import RequestContext
from django.template.loader import render_to_string
from django import template
from django.middleware.csrf import get_token

from cms.utils import is_editing
from cms import settings as cms_settings


register = template.Library()


def cms_editor(context):
    '''Lazily loads the cms editor. This should be called at the bottom of an html document to
       allow frontend editing. '''
    
    show_login = 'edit' in context['request'].GET
    return render_to_string("cms/cms/editor_script.html", {
        'cms_settings': cms_settings,
        'show_login': show_login,
    })

register.simple_tag(cms_editor, takes_context=True)



def cms_is_editing(context):
    return is_editing(context['request'])

register.assignment_tag(takes_context=True)(cms_is_editing)
