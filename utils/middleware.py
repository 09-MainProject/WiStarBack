# import hashlib
# import hmac
#
# from django.http import HttpResponseForbidden
# from django.middleware.csrf import CsrfViewMiddleware
#
# from config.settings import SECRET_KEY
#
#
# class CustomCSRFMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#         self.exempt_paths = [
#             '/api'     # 예: 토큰 발급 경로 등
#         ]
#         self.csrf_protected_paths = [
#             '/api/users/token/refresh',
#             '/api/users/logout'
#         ]
#
#     def __call__(self, request):
#
#         path = request.path
#
#         # 1️⃣ CSRF 검사 예외 처리
#         if any(path.startswith(exempt) for exempt in self.exempt_paths):
#             # 2️⃣ 특정 경로는 다시 CSRF 검사 수행
#             if path in self.csrf_protected_paths:
#                 return CsrfViewMiddleware(self.get_response)(request)
#             # 그 외 API는 CSRF 무시
#             return self.get_response(request)
#
#         # 기본 웹 요청은 기존 CSRF 처리
#         return CsrfViewMiddleware(self.get_response)(request)
#
#     # def is_valid(self, token):
#     #     try:
#     #         raw_token, signature = token.split('.')
#     #         expected_signature = hmac.new(SECRET_KEY.encode(), raw_token.encode(), hashlib.sha256).hexdigest()
#     #         return hmac.compare_digest(signature, expected_signature)
#     #     except Exception:
#     #         return False