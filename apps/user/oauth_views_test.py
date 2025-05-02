# import requests
# from django.conf import settings
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from django.shortcuts import redirect
#
# NAVER_TOKEN_URL = 'https://nid.naver.com/oauth2.0/token'
# NAVER_PROFILE_URL = 'https://openapi.naver.com/v1/nid/me'
#
# class NaverLoginCallbackView(APIView):
#     def get(self, request):
#         code = request.GET.get("code")
#         state = request.GET.get("state")
#
#         # 1. 네이버로부터 access_token 요청
#         token_res = requests.get(NAVER_TOKEN_URL, params={
#             "grant_type": "authorization_code",
#             "client_id": settings.NAVER_CLIENT_ID,
#             "client_secret": settings.NAVER_CLIENT_SECRET,
#             "code": code,
#             "state": state
#         })
#
#         access_token = token_res.json().get("access_token")
#
#         # 2. 네이버 프로필 요청
#         profile_res = requests.get(NAVER_PROFILE_URL, headers={
#             "Authorization": f"Bearer {access_token}"
#         })
#
#         naver_user = profile_res.json()["response"]
#         naver_id = naver_user["id"]
#         email = naver_user.get("email", "")
#
#         # 3. 유저 생성 or 로그인 처리 (User 모델에 저장)
#         user = YourUserModel.objects.get_or_create(
#             naver_id=naver_id, defaults={"email": email}
#         )[0]
#
#         # 4. JWT 토큰 발급
#         from rest_framework_simplejwt.tokens import RefreshToken
#         refresh = RefreshToken.for_user(user)
#         access = refresh.access_token
#
#         # 5. 프론트로 리다이렉트 + 토큰 전달
#         frontend_url = f"http://localhost:3000/social-login/callback?access={access}&refresh={refresh}"
#         return redirect(frontend_url)
