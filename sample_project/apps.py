from django.apps import AppConfig

class SampleProjectConfig(AppConfig):
    name = "sample_project"

    def ready(self):
        import sample_project.checks