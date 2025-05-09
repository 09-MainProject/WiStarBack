from drf_yasg import openapi

# 사용자 일정 및 팔로우 아이돌 일정 목록 조회 성공
SCHEDULE_LIST_SUCCESS = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING,
            example="사용자 + 팔로우 아이돌 일정 목록 조회 성공",
        ),
        "data": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_schedules": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT),
                ),
                "idol_schedules": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT),
                ),
            },
        ),
    },
)

# 일정 생성 성공
SCHEDULE_CREATE_SUCCESS = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=201),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING, example="사용자 일정 등록 성공"
        ),
        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
    },
)

# 일정 단건 조회 성공
SCHEDULE_DETAIL_SUCCESS = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING, example="사용자 일정 조회 성공"
        ),
        "data": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "uschedule_view": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
        ),
    },
)

# 일정 수정 성공
SCHEDULE_UPDATE_SUCCESS = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
        "message": openapi.Schema(type=openapi.TYPE_STRING, example="일정 수정 성공"),
        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
    },
)

# 일정 삭제 성공
SCHEDULE_DELETE_SUCCESS = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=204),
        "message": openapi.Schema(type=openapi.TYPE_STRING, example="일정 삭제 성공"),
        "data": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "schedule_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            },
        ),
    },
)

# 오류 응답
SCHEDULE_ERROR_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=400),
        "message": openapi.Schema(type=openapi.TYPE_STRING, example="권한이 없습니다."),
        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
    },
)
