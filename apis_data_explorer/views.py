from collections import OrderedDict
from datetime import date

from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.views.generic import ListView, TemplateView

from apis_data_projection.models import EntityFacet, EntityProjection


class HomeView(TemplateView):
    template_name = "apis_data_explorer/home.html"


class EntitySearchView(ListView):
    model = EntityProjection
    template_name = "apis_data_explorer/home.html"
    context_object_name = "results"
    paginate_by = 20

    MAX_VALUES_PER_FACET = 8
    EXPANDED_FACETS = 3

    FACET_OVERRIDES = {
        "gender": {"label": "Gender"},
        "nationality": {"label": "Nationality"},
        "confidence": {"label": "Confidence"},
    }

    EXCLUDED_FACETS = set()

    def get_query(self):
        return (self.request.GET.get("q") or "").strip()

    def get_date_from(self):
        return (self.request.GET.get("date_from") or "").strip()

    def get_date_to(self):
        return (self.request.GET.get("date_to") or "").strip()

    def get_base_queryset(self):
        return EntityProjection.objects.all()

    def apply_date_filters(self, qs):
        date_from = self.get_date_from()
        date_to = self.get_date_to()

        if date_from or date_to:
            qs = qs.exclude(start_date__isnull=True, end_date__isnull=True)

        if date_from and date_to:
            qs = qs.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=date_to),
                Q(end_date__isnull=True) | Q(end_date__gte=date_from),
            )
        elif date_from:
            qs = qs.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=date_from)
            )
        elif date_to:
            qs = qs.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=date_to)
            )

        return qs
    def get_search_queryset(self):
        qs = self.get_base_queryset()
        q = self.get_query()

        if not q:
            return self.apply_date_filters(qs.order_by("label", "id"))
        qs = (
            qs.filter(
                Q(label__icontains=q)
                | Q(search_text__icontains=q)
                | Q(entity_type__icontains=q)
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

        return self.apply_date_filters(qs)

    def get_selected_facets(self):
        selected = {}

        for key in self.request.GET.keys():
            if not key.startswith("facet__"):
                continue

            facet_name = key.removeprefix("facet__")
            values = [v.strip() for v in self.request.GET.getlist(key) if v.strip()]
            if values:
                selected[facet_name] = values

        return selected

    def apply_facet_filters(self, qs):
        selected_facets = self.get_selected_facets()

        for facet_name, values in selected_facets.items():
            qs = qs.filter(
                facets__name=facet_name,
                facets__value__in=values,
            )

        return qs.distinct()

    def get_queryset(self):
        return self.apply_facet_filters(self.get_search_queryset())

    def get_facets_for_panel(self):
        base_qs = self.get_search_queryset()

        if not base_qs.exists():
            return []

        rows = (
            EntityFacet.objects
            .filter(entity_projection_id__in=base_qs.values("id"))
            .exclude(name__in=self.EXCLUDED_FACETS)
            .values("kind", "name", "value")
            .annotate(count=Count("entity_projection_id", distinct=True))
            .order_by("kind", "name", "-count", "value")
        )

        selected_facets = self.get_selected_facets()
        grouped_by_kind = OrderedDict()

        for row in rows:
            kind = row["kind"] or "other"
            facet_name = row["name"]

            if kind not in grouped_by_kind:
                grouped_by_kind[kind] = {
                    "kind": kind,
                    "facets": OrderedDict(),
                }

            facets = grouped_by_kind[kind]["facets"]

            if facet_name not in facets:
                override = self.FACET_OVERRIDES.get(facet_name, {})
                facets[facet_name] = {
                    "name": facet_name,
                    "label": override.get("label", facet_name.replace("_", " ").title()),
                    "param": f"facet__{facet_name}",
                    "options": [],
                    "total_count": 0,
                    "is_selected": facet_name in selected_facets,
                }

            option = {
                "value": row["value"],
                "count": row["count"],
                "selected": row["value"] in selected_facets.get(facet_name, []),
            }

            facets[facet_name]["options"].append(option)
            facets[facet_name]["total_count"] += row["count"]

        all_facets = []
        for group in grouped_by_kind.values():
            for facet in group["facets"].values():
                selected_options = [o for o in facet["options"] if o["selected"]]
                unselected_options = [o for o in facet["options"] if not o["selected"]]

                visible_options = list(selected_options)
                for option in unselected_options:
                    if len(visible_options) >= self.MAX_VALUES_PER_FACET:
                        break
                    visible_options.append(option)

                visible_values = {o["value"] for o in visible_options}
                hidden_options = [
                    o for o in facet["options"] if o["value"] not in visible_values
                ]

                facet["visible_options"] = visible_options
                facet["hidden_options"] = hidden_options
                facet["has_more"] = bool(hidden_options)

                all_facets.append(
                    {
                        "kind": group["kind"],
                        "facet": facet,
                    }
                )

        all_facets.sort(
            key=lambda item: (
                0 if item["facet"]["is_selected"] else 1,
                -item["facet"]["total_count"],
                item["facet"]["label"].lower(),
            )
        )

        regrouped = OrderedDict()
        for index, item in enumerate(all_facets):
            kind = item["kind"]
            facet = item["facet"]

            if kind not in regrouped:
                regrouped[kind] = {
                    "kind": kind,
                    "facets": [],
                }

            facet["is_expanded"] = facet["is_selected"] or index < self.EXPANDED_FACETS
            regrouped[kind]["facets"].append(facet)

        return list(regrouped.values())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.get_query(),
                "date_from": self.get_date_from(),
                "date_to": self.get_date_to(),
                "selected_facets": self.get_selected_facets(),
                "facets": self.get_facets_for_panel(),
            }
        )
        return context