from django import template
from rango.models import Category

register = template.Library()

@register.inclusion_tag('rango/category_list.html')
def get_category_list(cat=None):
    return {'cat_list': Category.objects.all(), 'act_cat':cat}
