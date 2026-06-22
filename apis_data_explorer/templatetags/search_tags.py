from django import template
from apis_data_projection.models import EntityProjection

register = template.Library()

@register.simple_tag
def entity_types():
    entity_types_list = (
        EntityProjection.objects
        .values('entity_type')
        .distinct()
        .order_by('entity_type')
        .values_list('entity_type', flat=True)
    )
    print(entity_types_list)

    return entity_types_list
