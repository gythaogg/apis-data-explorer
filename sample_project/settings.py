from apis_acdhch_default_settings.settings import *
DEBUG = True

ROOT_URLCONF = "sample_project.urls"

INSTALLED_APPS.remove("apis_ontology")

ADDITIONAL_APPS = ["sample_project","apis_data_projection", "apis_data_explorer"]

for app in ADDITIONAL_APPS:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)


PROJECTION_SYNC_FACET_CONFIG = {
    "relation_excluded_fields": ["certainty"],
}
