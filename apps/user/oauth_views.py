# from urllib.parse import urlencode
#
# import requests
# from django.conf import settings
# from django.contrib.auth import get_user_model, login
# from django.core import signing
# from django.http import Http404
# from django.shortcuts import redirect, render
# from django.urls import reverse
# from django.views.generic import RedirectView
#
# # from member.forms import NicknameForm
#
# # [React] → [Django OAuth Redirect URL] → [Naver/GitHub] → [Django Callback] → [React로 토큰 전달]
#
#
# User = get_user_model()
#
# NAVER_CALLBACK_URL = "/users/naver/callback/"  # 애플리케이션 등록할 때 설정한 콜백 url  http://localhost:8000/oauth/naver/callback
# NAVER_STATE = "naver_login"  # oauth_urls.py/urlpatterns
# NAVER_LOGIN_URL = "https://nid.naver.com/oauth2.0/authorize"  # doc/api명세/로그은api명세  - 네이버 로그인 인증 요청 url
# NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"  # doc/api명세/로그은api명세  - 접근 토큰 발급/갱신/삭제 요청 url
# NAVER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"  # doc/api명세/회원 프로필 조회 api 명세  - 네이버 회원 프로필 조회
#
#
# # 네이버 로그인 인증 요청
# class NaverLoginRedirectView(RedirectView):
#
#     def get_redirect_url(self, *args, **kwargs):
#         # self.request.scheme - 요청의 프로토콜(스킴) - 값: 'http' 또는 'https'
#         # self.request.META.get('HTTP_HOST', '') - 브라우저가 접속한 도메인과 포트 - localhost:8000, 127.0.0.1:8000, mydomain.com 이런식의 브라우저 요청의 Host 헤더
#         domain = self.request.scheme + "://" + self.request.META.get("HTTP_HOST", "")
#         domain = domain.replace("localhost", "127.0.0.1")
#
#         callback_url = domain + NAVER_CALLBACK_URL
#         state = signing.dumps(NAVER_STATE)
#
#         # 필수 파라미터 설정
#         params = {
#             "response_type": "code",
#             "client_id": settings.NAVER_CLIENT_ID,
#             "redirect_uri": callback_url,
#             "state": state,
#         }
#
#         return f"{NAVER_LOGIN_URL}?{urlencode(params)}"
#
#
# # 네이버 접근 토큰 발급/갱신/삭제 요청
# def naver_callback(request):
#     code = request.GET.get("code")
#     state = request.GET.get("state")
#
#     if NAVER_STATE != signing.loads(state):
#         raise Http404
#
#     # 엑세스 토큰 발급
#     access_token = get_naver_access_token(code, state)
#
#     print("token request", access_token)
#
#     # 네이버 회원 프로필 조회
#     profile_response = get_naver_profile(access_token)
#
#     print("profile request", profile_response)
#     email = profile_response.get("email")
#     # print('email', email)
#
#     user = User.objects.filter(email=email).first()
#
#     # 유저가 있다면 로그인
#     if user:
#         # 유저가 활성화 되지 않았으면 활성화
#         if not user.is_active:
#             user.is_active = True
#             user.save()
#
#         login(request, user)
#         return redirect("main")
#
#     # 유저가 없으면 생성
#     return redirect(
#         reverse("oauth:nickname") + f"?access_token={access_token}&oauth=naver"
#     )
#
#
# # 새 사용자 등록 시, 닉네임을 입력받는 뷰
# def oauth_nickname(request):
#     access_token = request.GET.get("access_token")
#     oauth = request.GET.get("oauth")
#
#     if not access_token or oauth not in ["naver", "github"]:
#         return redirect("login")
#
#     form = NicknameForm(request.POST or None)
#
#     if form.is_valid():
#         user = form.save(commit=False)
#
#         if oauth == "naver":
#             profile = get_naver_profile(access_token)
#         else:
#             profile = get_github_profile(access_token)
#
#         email = profile.get("email")
#
#         # 이메일이 존재하면. 이미 가입했으면. 오류
#         if User.objects.filter(email=email).exists():
#             raise Http404
#
#         user.email = email
#
#         user.is_active = True
#         # user.set_password('1234')
#         random_password = User.objects.make_random_password()
#         print("random_password", random_password)  # naver QgCGBqeNWe github XQzwTvjtvZ
#         user.set_password(random_password)  # 왜 안돼!
#         user.save()
#
#         login(request, user)
#         return redirect("main")
#
#     return render(request, "auth/nickname.html", {"form": form})
#
#
# # 네이버 엑세스 토큰 발급
# def get_naver_access_token(code, state):
#     params = {
#         "grant_type": "authorization_code",
#         "client_id": settings.NAVER_CLIENT_ID,
#         "client_secret": settings.NAVER_CLIENT_SECRET,
#         "code": code,
#         "state": state,
#     }
#
#     # request : Django에서 클라이언트가 보낸 HTTP 요청 정보가 담긴 객체
#     # requests : 서버에서 다른 외부 서버(API)로 GET, POST 요청을 보낼 때 사용
#
#     # 접근 토큰 발급 요청
#     # 요청 후 각 토큰을 발급 받음 refresh_token , access_token
#     response = requests.get(NAVER_TOKEN_URL, params=params)
#     result = response.json()
#     return result.get("access_token")
#
#
# # 네이버 회원 프로필 조회
# def get_naver_profile(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#
#     # 네이버 회원 프로필 조회 요청
#     response = requests.get(NAVER_PROFILE_URL, headers=headers)
#
#     if response.status_code != 200:
#         raise Http404
#
#     result = response.json()
#     return result.get("response")
