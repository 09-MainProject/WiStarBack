import pytest
from django.core import signing
from django.core.signing import TimestampSigner
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return User.objects.create_user(**kwargs)

    return make_user


@pytest.mark.django_db
def test_register_user(api_client):
    url = reverse("users:register")  # URL name이 'users:register'라고 가정합니다.
    data = {
        "email": "test@example.com",
        "password": "password123",
        "nickname": "testuser",
        "name": "테스트",
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "verify_url" in response.data


@pytest.mark.django_db
def test_verify_email(api_client, create_user):
    user = create_user(
        email="verifytest@example.com", password="password123", is_active=False
    )

    signer = TimestampSigner()
    signed_email = signer.sign(user.email)
    signed_code = signing.dumps(signed_email)

    url = reverse("users:verify_email") + f"?code={signed_code}"
    response = api_client.get(url)

    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert user.is_active is True


@pytest.mark.django_db
def test_login_user(api_client, create_user):
    password = "password123"
    user = create_user(email="loginuser@example.com", password=password, is_active=True)

    url = reverse("users:token_obtain_pair")
    data = {"email": user.email, "password": password}
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]


@pytest.mark.django_db
def test_logout_user(api_client, create_user):
    password = "password123"
    user = create_user(email="logout@example.com", password=password, is_active=True)

    # 로그인해서 쿠키 세팅
    login_url = reverse("users:token_obtain_pair")
    login_data = {"email": user.email, "password": password}
    login_response = api_client.post(login_url, login_data)
    refresh_token = login_response.cookies.get("refresh_token").value

    api_client.cookies["refresh_token"] = refresh_token

    logout_url = reverse("users:logout")
    api_client.force_authenticate(user=user)
    response = api_client.post(logout_url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_token_refresh(api_client, create_user):
    password = "password123"
    user = create_user(
        email="refreshtest@example.com", password=password, is_active=True
    )

    login_url = reverse("users:token_obtain_pair")
    login_data = {"email": user.email, "password": password}
    login_response = api_client.post(login_url, login_data)

    refresh_token = login_response.cookies.get("refresh_token").value
    csrf_token = login_response.data["data"]["csrf_token"]

    api_client.cookies["refresh_token"] = refresh_token

    refresh_url = reverse("users:token_refresh")
    headers = {"HTTP_X_CSRFTOKEN": csrf_token}

    response = api_client.post(refresh_url, **headers)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]


@pytest.mark.django_db
def test_profile_view_update_delete(api_client, create_user):
    password = "password123"
    user = create_user(
        email="profile@example.com",
        password=password,
        nickname="OldNickname",
        name="OldName",
        is_active=True,
    )

    login_url = reverse("users:token_obtain_pair")
    login_data = {"email": user.email, "password": password}
    login_response = api_client.post(login_url, login_data)

    access_token = login_response.data["data"]["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # GET 프로필 조회
    profile_url = reverse("users:profile")
    response = api_client.get(profile_url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["nickname"] == "OldNickname"

    # PATCH 프로필 수정
    update_data = {"nickname": "NewNickname"}
    response = api_client.patch(profile_url, update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["nickname"] == "NewNickname"

    # DELETE 회원 탈퇴
    response = api_client.delete(profile_url)
    assert response.status_code == status.HTTP_200_OK
    assert User.objects.filter(email=user.email).exists() is False
