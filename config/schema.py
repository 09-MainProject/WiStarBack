from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

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
)

# 자동 swagger 문서화 패키지
# https://drf-yasg.readthedocs.io/en/stable/
# https://drf-yasg.readthedocs.io/en/stable/readme.html
#
# 설치
# poetry add drf-yasg
