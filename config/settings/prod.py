import random

from dotenv import dotenv_values

from .base import *  # noqa: F403

# DEBUG = True
# ALLOWED_HOSTS = []

DEBUG = False
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    # "EC2 퍼블릭 IP",  # EC2 퍼블릭 IP
]


# dotenv_values 메서드는 env 파일의 경로를 파라미터로 전달 받아 해당 파일을 읽어온 후 Key, Value 형태로 매핑하여 dict로 반환합니다.
ENV = dotenv_values(BASE_DIR / "envs/prod.env")  # noqa: F405

# 시크릿 키를 ENV 변수에 저장된 딕셔너리에서 가져옵니다. 만약 파일에서 읽어온 시크릿 키가 존재하지 않는다면 50자리의 무작위 문자열을 반환합니다.
SECRET_KEY = ENV.get(
    "DJANGO_SECRET_KEY", "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()?", k=50))
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": ENV.get("POSTGRES_HOST", "db"),
        "USER": ENV.get("POSTGRES_USER", "postgres"),
        "PASSWORD": ENV.get("POSTGRES_PASSWORD", "postgres"),
        "NAME": ENV.get("POSTGRES_DB", "oz_collabo"),
        "PORT": ENV.get("POSTGRES_PORT", 5432),
    }
}
