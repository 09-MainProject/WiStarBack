from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.post.models import Post, Comment

User = get_user_model()

class PostTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="password123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123"
        )
        self.client.force_authenticate(user=self.user)

        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            author=self.user
        )

    def test_create_post(self):
        """게시글 생성 테스트"""
        url = reverse('post-list')
        data = {
            "title": "새 게시글",
            "content": "새 게시글 내용입니다."
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author']['username'], self.user.username)

    def test_retrieve_post(self):
        """게시글 조회 테스트"""
        url = reverse('post-detail', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post.title)

    def test_update_post(self):
        """게시글 수정 테스트"""
        url = reverse('post-detail', args=[self.post.id])
        data = {
            "title": "수정된 제목",
            "content": "이것은 수정된 게시글의 내용입니다. 10자 이상으로 작성했습니다."
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "수정된 제목")

    def test_update_post_unauthorized(self):
        """다른 사용자의 게시글 수정 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('post-detail', args=[self.post.id])
        data = {
            "title": "수정된 제목",
            "content": "이것은 수정된 게시글의 내용입니다. 10자 이상으로 작성했습니다."
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post(self):
        """게시글 삭제(소프트 딜리트) 테스트"""
        url = reverse('post-detail', args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_delete_post_by_admin(self):
        """관리자의 게시글 삭제 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('post-detail', args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_delete_post_unauthorized(self):
        """다른 사용자의 게시글 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('post-detail', args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_increase_post_views(self):
        """게시글 조회수 증가 테스트"""
        url = reverse('post-increase-views', args=[self.post.id])
        original_views = self.post.views
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, original_views + 1)

    def test_create_post_with_image(self):
        """이미지가 포함된 게시글 생성 테스트"""
        url = reverse('post-list')
        # 테스트용 이미지 파일 생성
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        data = {
            "title": "이미지가 있는 게시글",
            "content": "이미지가 포함된 게시글 내용입니다. 10자 이상으로 작성했습니다.",
            "image": image
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['image'])
        self.assertEqual(response.data['title'], "이미지가 있는 게시글")

    def test_create_post_with_invalid_image(self):
        """잘못된 이미지로 게시글 생성 시도 테스트"""
        url = reverse('post-list')
        # 잘못된 형식의 파일 생성
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        data = {
            "title": "잘못된 이미지 게시글",
            "content": "잘못된 이미지가 포함된 게시글 내용입니다. 10자 이상으로 작성했습니다.",
            "image": invalid_file
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)