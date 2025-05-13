from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.conf import settings
from drf_yasg.generators import OpenAPISchemaGenerator


class ExcludeAppsSchemaGenerator(OpenAPISchemaGenerator):
    EXCLUDED_APPS = getattr(settings, "SWAGGER_EXCLUDED_APPS", [])

    def get_endpoints(self, request):
        endpoints = super().get_endpoints(request)
        filtered = {}
        for path, (view_cls, path_regex, method_map) in endpoints.items():
            if not any(view_cls.__module__.startswith(app) for app in self.EXCLUDED_APPS):
                filtered[path] = (view_cls, path_regex, method_map)
        return filtered


# 스웨거 초기화
schema_view = get_schema_view(
    openapi.Info(
        title="WiStar API",
        default_version="v1",
        description="WiStar API 문서",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="xowls0131@naver.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[
        permissions.AllowAny,
    ],
    generator_class=ExcludeAppsSchemaGenerator,
)



# 자동 swagger 문서화 패키지
# https://drf-yasg.readthedocs.io/en/stable/
# https://drf-yasg.readthedocs.io/en/stable/readme.html
#
# 설치
# poetry add drf-yasg



# 특정 앱 스웨거 비활성화 설정하는 클래스
# class ExcludeAppsSchemaGenerator(OpenAPISchemaGenerator):
#     EXCLUDED_APPS = getattr(settings, "SWAGGER_EXCLUDED_APPS", [])
#
#     def get_endpoints(self, request):
#         """기존 get_endpoints 결과에서 특정 앱에 해당하는 endpoint 제거"""
#         endpoints = super().get_endpoints(request)
#         filtered = {}
#         for path, (view_cls, path_regex, method_map) in endpoints.items():
#             if not any(view_cls.__module__.startswith(app) for app in self.EXCLUDED_APPS):
#                 filtered[path] = (view_cls, path_regex, method_map)
#         return filtered