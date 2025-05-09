# from abc import abstractmethod
#
# import requests
# from django.contrib.auth import get_user_model
# from requests import Response
# from rest_framework import status
# from rest_framework.permissions import AllowAny
# from rest_framework_simplejwt.tokens import RefreshToken
#
# from apps.user.oauth_mixins_test import KaKaoProviderInfoMixin, GoogleProviderInfoMixin, NaverProviderInfoMixin
#
# User = get_user_model()
#
# class OAuthLoginView:
#     pass
#
# class OAuthCallbackView(OAuthLoginView):
#     permission_classes = [AllowAny]
#
#     @abstractmethod
#     def get_provider_info(self):
#         pass
#
#     def post(self, request, *args, **kwargs):
#         # 프론트엔드에서 Post 요청을 보낼 때 파라미터 또는 바디값에서 code를 가져옴
#         code = request.data.get("code")
#         # code 값이 없으면 400 에러와 함께 에러메시지를 반환
#         if not code:
#             return Response({"msg": "인가코드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#         # 소셜로그인에 필요한 redirect_uri, client_id, grant_type 등의 provider_info 를 가져옴
#         provider_info = self.get_provider_info()
#
#         # Oauth2 서버에 provider_info 와 code를 파라미터로 사용하여 token_url로 POST 요청을 보냄
#         token_response = self.get_token(code, provider_info)
#
#         # Oauth2 서버 응답에 대한 예외처리
#         if token_response.status_code != status.HTTP_200_OK:
#             return Response(
#                 {"msg": f"{provider_info['name']} 서버로 부터 토큰을 받아오는데 실패하였습니다."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         # 토큰 요청에 대한 응답으로 부터 access_token을 가져옴
#         access_token = token_response.json().get("access_token")
#
#         # 가져온 access_token과 provider_info를 파라미터로 사용하여 profile_url에 소셜로그인 프로필 정보 조회 GET 요청을 보냄
#         profile_response = self.get_profile(access_token, provider_info)
#
#         # 프로필 요청 조회 실패시 예외처리
#         if profile_response.status_code != status.HTTP_200_OK:
#             return Response(
#                 {"msg": f"{provider_info['name']} 서버로 부터 프로필 데이터를 받아오는데 실패하였습니다."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         # 프로필 가져오기에 성공하면 가져온 프로필 데이터, provider_info를 사용하여 서비스 로그인 처리.
#         return self.login_process_user(request, profile_response.json(), provider_info)
#
#     def get_token(self, code, provider_info):
#         '''
#         requests 라이브러리를 활용하여 Oauth2 API 플랫폼에 액세스 토큰을 요청하는 함수
#         '''
#
#         return requests.post(
#             provider_info["token_url"],
#             headers={"Content-Type": "application/x-www-form-urlencoded"},
#             data={
#                 "grant_type": "authorization_code",
#                 "code": code,
#                 "redirect_uri": self.get_callback_url(provider_info=provider_info),
#                 "client_id": provider_info["client_id"],
#                 "client_secret": provider_info.get("client_secret"),
#             },
#         )
#
#     def get_profile(self, access_token, provider_info):
#         '''
#         requests 라이브러리를 활용하여 Oauth2 API 플랫폼에 액세스 토큰을 사용하여 프로필 정보 조회를 요청하는 함수
#         '''
#
#         return requests.get(
#             provider_info["profile_url"],
#             headers={
#                 "Authorization": f"Bearer {access_token}",
#                 "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
#             },
#         )
#
#     def login_process_user(self, request, profile_res_data, provider_info):
#         '''
#         Oauth2 API 플랫폼에서 가져온 프로필을 바탕으로 서비스 내의 유저 객체를 생성하고 로그인 과정을 진행합니다.
#         응답으로는 access_token을 바디값으로, refresh_token을 쿠키값으로 내려줍니다.
#         '''
#
#         email, nickname = self.get_user_data(provider_info, profile_res_data)
#
#         try:
#             user = User.objects.get(email=email)
#         except User.DoesNotExist:
#             user = User.objects.create_oauth_user(email=email, nickname=nickname)
#
#         refresh_token = RefreshToken.for_user(user)
#         response_data = {
#             "email": user.email,
#             "nickname": user.nickname,
#             "access_token": str(refresh_token.access_token)
#         }
#
#         response = Response(response_data, status=status.HTTP_200_OK)
#         response.set_cookie("refresh", str(refresh_token))
#
#         return response
#
#
# def get_user_data(self, provider_info, profile_res_data):
#     '''
#     Oauth2 API 플랫폼에서 가져온 프로필을 데이터 스키마에서 필요한 데이터를 추출하는 함수입니다.
#     '''
#     # 각 provider의 프로필 데이터 처리 로직
#
#
#     if provider_info["name"] == "구글":
#         email = profile_res_data.get(provider_info["email_field"])
#         nickname = profile_res_data.get(provider_info["nickname_field"])
#         return email, nickname
#
#     elif provider_info["name"] == "네이버":
#         profile_data = profile_res_data.get("response")
#         email = profile_data.get(provider_info["email_field"])
#         nickname = profile_data.get(provider_info["nickname_field"])
#         return email, nickname
#
#     elif provider_info["name"] == "카카오":
#         account_data = profile_res_data.get("kakao_account")
#         email = account_data.get(provider_info["email_field"])
#         profile_data = account_data.get("profile")
#         nickname = profile_data.get(provider_info["nickname_field"])
#         return email, nickname
#
#
# class KakaoCallbackView(KaKaoProviderInfoMixin, OAuthCallbackView):
#     pass
#
#
# class GoogleCallbackView(GoogleProviderInfoMixin, OAuthCallbackView):
#     pass
#
#
# class NaverCallbackView(NaverProviderInfoMixin, OAuthCallbackView):
#     pass
