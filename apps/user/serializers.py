from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from utils.exceptions import CustomAPIException
from utils.responses.user import INVALID_REFRESH_TOKEN

User = get_user_model()


class UsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["nickname", "name"]


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "password_confirm", "name", "nickname"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {
                "write_only": True
            },  # write_only : 쓰기만 되고 읽어 오진 않음.
            # "phone_number": {"required": False, "allow_blank": True}
        }

    # 데이터 검증
    def validate(self, data):
        # 비밀번호 일치 여부 확인
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "비밀번호가 일치하지 않습니다."}
            )
        data.pop("password_confirm")  # 모델에 없는 필드 제거

        user = User(**data)

        # errors = dict()  # 에러 여러개를 대비한 처리용
        try:
            # validate_password는 settings.py에 AUTH_PASSWORD_VALIDATORS 설정된 조건을 만족하는지 검사
            validate_password(password=data["password"], user=user)
        # 에러 여러개를 대비한 처리
        # except ValidationError as e:
        #     errors['password'] = list(e.messages)
        # if errors:
        #     raise serializers.ValidationError(errors)

        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return super().validate(data)

    def create(self, validated_data):
        # create_user() -> 비밀번호 해싱
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            nickname=validated_data["nickname"],
        )
        return user


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh_token"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)  # 토큰이 유효한지 검사됨
            print(f"토큰 타입: {token.get('token_type')}")  # 디코드된 토큰 타입 확인
            token.blacklist()  # 블랙리스트 등록
        except Exception:
            raise CustomAPIException(INVALID_REFRESH_TOKEN)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password", "name", "nickname"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {
                "write_only": True
            },  # write_only : 쓰기만 되고 읽어 오진 않음.
            # "phone_number": {"required": False, "allow_blank": True}
        }

    def update(self, instance, validated_data):
        if password := validated_data.get("password"):
            validated_data["password"] = make_password(password)
        return super().update(instance, validated_data)
