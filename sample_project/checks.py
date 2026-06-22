from __future__ import annotations
from xml.parsers.expat import errors

from django.core.checks import Error, Warning, register

@register()
def sample_project_checks(**kwargs):
    errors = []

    try:
        from faker import Faker
    except Exception as exc:
        errors.append(
            Warning(
                "Faker could not be imported.",
                hint="Install Faker if you need to use the `populate_sample_data` management command.",
                id="sample_project.E001",
                obj=exc,
            )
        )
    return errors
