# utils/swagger.py
from drf_yasg.generators import OpenAPISchemaGenerator

class ExcludeAppsSchemaGenerator(OpenAPISchemaGenerator):
    EXCLUDED_APPS = ["apps.post", "apps.user_schedule", "apps.idol_schedule"]  # 제외할 앱 이름

    def get_endpoints(self, request):
        """기존 get_endpoints 결과에서 특정 앱에 해당하는 endpoint 제거"""
        endpoints = super().get_endpoints(request)
        filtered = {}
        for path, (view_cls, path_regex, method_map) in endpoints.items():
            if not any(view_cls.__module__.startswith(app) for app in self.EXCLUDED_APPS):
                filtered[path] = (view_cls, path_regex, method_map)
        return filtered
