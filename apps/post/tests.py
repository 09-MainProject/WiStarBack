import io
import os

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.image.models import Image as ImageModel
from apps.like.models import Like

from .models import Post

User = get_user_model()


class PostTests(TestCase):
    def setUp(self):
        """테스트를 위한 기본 설정"""
        self.client = APIClient()

        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            nickname="testuser",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            name="Other User",
            nickname="otheruser",
        )

        # 테스트용 게시물 생성
        self.post = Post.objects.create(
            title="Test Post", content="This is a test post.", author=self.user
        )

        # 사용자 인증
        self.client.force_authenticate(user=self.user)

        # 테스트용 이미지 생성
        self.image = self.create_test_image()

        # ContentType 설정
        self.post_content_type = ContentType.objects.get_for_model(Post)

    def create_test_image(self):
        """테스트용 이미지 파일을 생성합니다."""
        file = io.BytesIO()
        image = Image.new("RGB", (100, 100), "white")
        image.save(file, "png")
        file.name = "test.png"
        file.seek(0)
        return SimpleUploadedFile(
            name="test.png", content=file.read(), content_type="image/png"
        )

    def tearDown(self):
        """테스트 후 정리"""
        # 테스트 이미지 파일 정리
        if hasattr(self, "image"):
            if os.path.exists(self.image.name):
                os.remove(self.image.name)

    def test_create_post(self):
        """게시물 생성 테스트"""
        url = reverse("post-list")
        data = {"title": "새 게시글", "content": "새 내용입니다."}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data["title"], data["title"])
        self.assertEqual(response.data["content"], data["content"])
        self.assertEqual(response.data["author"], self.user.nickname)

    def test_retrieve_post(self):
        """게시물 조회 테스트"""
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post.title)
        self.assertEqual(response.data["content"], self.post.content)

    def test_retrieve_post_detail(self):
        """게시물 상세 조회 테스트"""
        # GenericForeignKey를 사용하여 Like 생성
        Like.objects.create(
            content_type=self.post_content_type, object_id=self.post.id, user=self.user
        )
        Like.objects.create(
            content_type=self.post_content_type,
            object_id=self.post.id,
            user=self.other_user,
        )
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post.title)
        self.assertEqual(response.data["content"], self.post.content)
        self.assertIn("author", response.data)
        self.assertEqual(response.data["author"], self.user.nickname)
        self.assertIn("likes_count", response.data)
        self.assertEqual(response.data["likes_count"], 2)
        self.assertIn("is_liked", response.data)
        self.assertTrue(response.data["is_liked"])
        self.assertIn("views", response.data)
        self.assertEqual(response.data["views"], 1)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        self.assertIn("is_deleted", response.data)
        self.assertFalse(response.data["is_deleted"])

    def test_retrieve_post_detail_other_user(self):
        """다른 사용자의 게시물 상세 조회 테스트"""
        Like.objects.create(
            content_type=self.post_content_type, object_id=self.post.id, user=self.user
        )
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.get(url)
        self.assertIn("is_liked", response.data)
        self.assertFalse(response.data["is_liked"])

    def test_retrieve_deleted_post(self):
        """삭제된 게시물 조회 테스트"""
        self.post.is_deleted = True
        self.post.save()
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post(self):
        """게시물 수정 테스트"""
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        data = {"content": "수정된 내용"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, data["content"])

    def test_update_post_unauthorized(self):
        """다른 사용자의 게시물 수정 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        data = {
            "content": "Unauthorized Update",
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post(self):
        """게시물 삭제(소프트 딜리트) 테스트"""
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_delete_post_unauthorized(self):
        """다른 사용자의 게시물 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_posts(self):
        """게시물 목록 조회 테스트"""
        url = reverse("post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)

    def test_create_post_unauthenticated(self):
        """인증되지 않은 사용자의 게시물 작성 시도 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("post-list")
        data = {
            "title": "Unauthenticated Post",
            "content": "This is an unauthenticated post.",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_post(self):
        """게시물 좋아요 테스트"""
        url = reverse("post-likes", kwargs={"pk": self.post.id})
        response = self.client.post(url)
        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED]
        )
        if response.data:
            self.assertIn("status", response.data)

    def test_unlike_post(self):
        """게시물 좋아요 취소 테스트"""
        Like.objects.create(
            content_type=self.post_content_type, object_id=self.post.id, user=self.user
        )
        url = reverse("post-likes", kwargs={"pk": self.post.id})
        response = self.client.delete(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT],
        )
        if response.data:
            self.assertIn("status", response.data)

    def test_increase_post_views(self):
        """게시물 조회수 증가 테스트"""
        initial_views = self.post.views
        url = reverse("post-detail", kwargs={"pk": self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, initial_views + 1)
