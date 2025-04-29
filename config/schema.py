from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Blog API",
        default_version="v1",
        description="Django REST Framework API document",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[
        permissions.AllowAny,
    ],
)

# 자동 swagger 문서화 패키지
# https://drf-yasg.readthedocs.io/en/stable/
# https://drf-yasg.readthedocs.io/en/stable/readme.html
#
# 설치
# poetry add drf-yasg