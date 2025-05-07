from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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

    def test_create_post(self):
        """게시물 생성 테스트"""
        url = reverse("post-list")
        data = {"title": "New Test Post", "content": "This is a new test post."}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data["title"], data["title"])
        self.assertEqual(response.data["content"], data["content"])
        self.assertEqual(response.data["author"]["nickname"], self.user.nickname)

    def test_retrieve_post(self):
        """게시물 조회 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post.title)
        self.assertEqual(response.data["content"], self.post.content)

    def test_retrieve_post_detail(self):
        """게시물 상세 조회 테스트"""
        # 좋아요 추가
        self.post.likes.add(self.user, self.other_user)

        url = reverse("post-detail", args=[self.post.id])
        response = self.client.get(url)

        # 기본 정보 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post.title)
        self.assertEqual(response.data["content"], self.post.content)

        # 작성자 정보 확인
        self.assertIn("author", response.data)
        self.assertEqual(response.data["author"]["nickname"], self.user.nickname)
        self.assertEqual(response.data["author"]["name"], self.user.name)

        # 좋아요 정보 확인
        self.assertIn("likes_count", response.data)
        self.assertEqual(response.data["likes_count"], 2)
        self.assertIn("is_liked", response.data)
        self.assertTrue(response.data["is_liked"])

        # 조회수 확인
        self.assertIn("views", response.data)
        self.assertEqual(response.data["views"], 1)

        # 생성/수정 시간 확인
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

        # 삭제 여부 확인
        self.assertIn("is_deleted", response.data)
        self.assertFalse(response.data["is_deleted"])

    def test_retrieve_post_detail_other_user(self):
        """다른 사용자의 게시물 상세 조회 테스트"""
        # 좋아요 추가
        self.post.likes.add(self.user)

        # 다른 사용자로 인증
        self.client.force_authenticate(user=self.other_user)

        url = reverse("post-detail", args=[self.post.id])
        response = self.client.get(url)

        # 좋아요 여부 확인
        self.assertIn("is_liked", response.data)
        self.assertFalse(response.data["is_liked"])

    def test_retrieve_deleted_post(self):
        """삭제된 게시물 조회 테스트"""
        self.post.is_deleted = True
        self.post.save()

        url = reverse("post-detail", args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post(self):
        """게시물 수정 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        data = {"title": "Updated Post", "content": "This is an updated post."}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, data["title"])
        self.assertEqual(self.post.content, data["content"])

    def test_update_post_unauthorized(self):
        """다른 사용자의 게시물 수정 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", args=[self.post.id])
        data = {
            "title": "Unauthorized Update",
            "content": "This is an unauthorized update.",
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post(self):
        """게시물 삭제(소프트 딜리트) 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_delete_post_unauthorized(self):
        """다른 사용자의 게시물 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_posts(self):
        """게시물 목록 조회 테스트"""
        url = reverse("post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_post_unauthenticated(self):
        """인증되지 않은 사용자의 게시물 작성 시도 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("post-list")
        data = {
            "title": "Unauthenticated Post",
            "content": "This is an unauthenticated post.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_post(self):
        """게시물 좋아요 테스트"""
        url = reverse("post-like", args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "liked")
        self.assertTrue(self.post.likes.filter(id=self.user.id).exists())

    def test_unlike_post(self):
        """게시물 좋아요 취소 테스트"""
        self.post.likes.add(self.user)
        url = reverse("post-like", args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "unliked")
        self.assertFalse(self.post.likes.filter(id=self.user.id).exists())

    def test_increase_post_views(self):
        """게시물 조회수 증가 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)
