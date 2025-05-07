from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase

from apps.post.models import Post
from apps.user.models import User

from .models import Like


class LikeTests(APITestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            nickname="testuser",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            name="Other User",
            nickname="otheruser",
        )

        # 테스트용 게시물 생성
        self.post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user,
        )

        # ContentType 설정
        self.post_content_type = ContentType.objects.get_for_model(Post)

        # URL 설정
        self.like_list_url = f"/api/{self.post_content_type.app_label}/{self.post.id}/likes"
        self.like_detail_url = (
            lambda pk: f"/api/{self.post_content_type.app_label}/{self.post.id}/likes/{pk}"
        )

    def test_create_like(self):
        """좋아요 생성 테스트"""
        self.client.force_authenticate(user=self.user)
        data = {
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.like_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), 1)

    def test_create_like_unauthenticated(self):
        """인증되지 않은 사용자의 좋아요 생성 테스트"""
        data = {
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.like_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_like(self):
        """좋아요 삭제 테스트"""
        self.client.force_authenticate(user=self.user)
        # 좋아요 생성
        like = Like.objects.create(
            user=self.user,
            content_type=self.post_content_type,
            object_id=self.post.id,
        )

        # 좋아요 삭제
        response = self.client.delete(self.like_detail_url(like.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Like.objects.count(), 0)

    def test_delete_like_unauthorized(self):
        """권한 없는 사용자의 좋아요 삭제 테스트"""
        self.client.force_authenticate(user=self.user)
        # 좋아요 생성
        like = Like.objects.create(
            user=self.user,
            content_type=self.post_content_type,
            object_id=self.post.id,
        )

        # 다른 사용자로 로그인
        self.client.force_authenticate(user=self.other_user)

        # 좋아요 삭제 시도
        response = self.client.delete(self.like_detail_url(like.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Like.objects.count(), 1)

    def test_list_likes(self):
        """좋아요 목록 조회 테스트"""
        self.client.force_authenticate(user=self.user)
        # 좋아요 생성
        Like.objects.create(
            user=self.user,
            content_type=self.post_content_type,
            object_id=self.post.id,
        )

        response = self.client.get(self.like_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
