from django import template
import os
from django.conf import settings

register = template.Library()

@register.filter
def get_building_image(building_name):
    static_path = f'/static/images/building_{building_name}.jpg'
    absolute_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'building_{building_name}.jpg')
    if os.path.exists(absolute_path):
        return static_path
    return '/static/images/default_building.jpg'
