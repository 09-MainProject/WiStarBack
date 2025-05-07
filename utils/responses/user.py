# fmt: off

# 회원가입
SIGNUP_SUCCESS = {
    "code": 201,
    "message": "회원가입이 완료되었습니다.",
    "data": None,
}
SIGNUP_FAILED = {
    "code": 200,
    "message": "회원가입을 실패하였습니다.",
    "data": None,
}
SIGNUP_PASSWORD_MISMATCH = {
    "code": 400,
    "message": "비밀번호가 일치하지 않습니다.",
    "data": None,
}
WEAK_PASSWORD = {
    "code": 400,
    "message": "비밀번호가 보안 기준을 만족하지 않습니다.",
    "data": None,
}
DUPLICATE_EMAIL = {
    "code": 400,
    "message": "이미 존재하는 이메일입니다.",
    "data": None
}

DUPLICATE_NICKNAME = {
    "code": 400,
    "message": "이미 존재하는 닉네임입니다.",
    "data": None
}

# EMAIL_NOT_VERIFIED = {
#     "code": 400,
#     "message": "이메일 인증이 완료되지 않았습니다.",
#     "data": None
# }
# SOCIAL_LOGIN_FAILED = {
#     "code": 400,
#     "message": "소셜 로그인에 실패했습니다.",
#     "data": None
# }

# 이메일 인증
VERIFY_EMAIL_SUCCESS = {
    "code": 200,
    "message": "이메일 인증이 완료되었습니다.",
    "data": None,
}
SIGNATURE_EXPIRED = {
    "code": 410,
    "message": "인증 링크가 만료되었습니다.",
    "data": None,
}
INVALID_SIGNATURE = {
    "code": 400,
    "message": "유효하지 않은 인증 코드입니다.",
    "data": None,
}

# 로그인 로그아웃
LOGIN_SUCCESS = {
    "code": 200,
    "message": "로그인을 성공했습니다.",
    "data": None,
}
LOGIN_FAILED = {
    "code": 401,
    "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "data": None,
}
LOGOUT_SUCCESS = {
    "code": 200,
    "message": "로그아웃되었습니다.",
    "data": None,
}

# CSRF토큰
CSRF_VALIDATION_FAILED = {
    "code": 403,
    "message": "CSRF 검증을 실패했습니다",
    "data": None,
}
CSRF_INVALID_TOKEN = {
    "code": 403,
    "message": "유효하지 않은 CSRF 토큰입니다.",
    "data": None,
}

# Refresh 토큰
INVALID_REFRESH_TOKEN = {
    "code": 401,
    "message": "유효하지 않은 리프레시 토큰입니다.",
    "data": None,
}
MISSING_REFRESH_TOKEN = {
    "code": 401,
    "message": "리프레시 토큰이 없습니다.",
    "data": None,
}
TOKEN_REFRESH_RESPONSE = {
    "code": 200,
    "message": "액세스 토큰이 재발급되었습니다.",
    "data": None,
}

# 회원 삭제
DELETE_SUCCESS = {
    "code": 200,
    "message": "유저 삭제를 성공했습니다.",
    "data": None,
}

# ValidationError	유효성 검증 실패	400
# NotAuthenticated	인증 안 됨	401
# PermissionDenied	권한 없음	403
# NotFound	리소스 없음	404
# APIException	기본 Exception (상태코드 500)	500
