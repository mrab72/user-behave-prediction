#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.apps import AppConfig
from django.conf import settings as project_settings


class DpuConfig(AppConfig):
    name = 'tubp.apps.dpu'
    verbose_name = "Dpu"

    def ready(self):
        import tubp.apps.dpu.settings as app_settings
        for name in dir(app_settings):
            if name.isupper() and not hasattr(project_settings, name):
                setattr(project_settings, name, getattr(app_settings, name))
