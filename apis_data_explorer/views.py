from django.views.generic import TemplateView
from django.db.models import Q, Case, When, Value, IntegerField
from django.views.generic import ListView

from apis_data_projection.models import EntityProjection


class HomeView(TemplateView):
    template_name = "apis_data_explorer/home.html"

class EntitySearchView(ListView):
    model = EntityProjection
    template_name = "apis_data_explorer/home.html"
    context_object_name = "results"
    paginate_by = 20

    def get_query(self):
        return (self.request.GET.get("q") or "").strip()

    def get_selected_entity_type(self):
        return (self.request.GET.get("entity_type") or "").strip()

    def get_base_queryset(self):
        return EntityProjection.objects.all()

    def get_queryset(self):
        qs = self.get_base_queryset()
        q = self.get_query()
        selected_entity_type = self.get_selected_entity_type()

        if selected_entity_type:
            qs = qs.filter(entity_type=selected_entity_type)

        if not q:
            return qs.none()

        qs = (
            qs.filter(
                Q(label__icontains=q) |
                Q(search_text__icontains=q) |
                Q(entity_type__icontains=q)
            )
            .annotate(
                relevance=Case(
                    When(label__iexact=q, then=Value(100)),
                    When(label__istartswith=q, then=Value(80)),
                    When(label__icontains=q, then=Value(60)),
                    When(entity_type__iexact=q, then=Value(40)),
                    When(entity_type__istartswith=q, then=Value(30)),
                    When(search_text__icontains=q, then=Value(10)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("-relevance", "label", "id")
        )

        return qs

    def get_entity_types(self):
        return list(
            EntityProjection.objects
            .values_list("entity_type", flat=True)
            .order_by("entity_type")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entity_types = self.get_entity_types()

        context.update({
            "query": self.get_query(),
            "selected_entity_type": self.get_selected_entity_type(),
            "entity_types": entity_types,
            "entity_type_placeholder": ", ".join(entity_types),
        })
        return context