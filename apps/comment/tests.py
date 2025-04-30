from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.post.models import Post
from .models import Comment

User = get_user_model()

class CommentTests(TestCase):
    def setUp(self):
        """테스트를 위한 기본 설정"""
        self.client = APIClient()
        
        # 테스트용 사용자 생성
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
        
        # 테스트용 게시물 생성
        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            author=self.user
        )
        
        # 테스트용 댓글 생성
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="This is a test comment."
        )
        
        # 사용자 인증
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        """댓글 생성 테스트"""
        url = reverse('comment-list', args=[self.post.id])
        data = {
            "content": "새로운 댓글입니다."
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(response.data['author']['username'], self.user.username)

    def test_retrieve_comment(self):
        """댓글 조회 테스트"""
        url = reverse('comment-detail', args=[self.post.id, self.comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], self.comment.content)

    def test_update_comment(self):
        """댓글 수정 테스트"""
        url = reverse('comment-detail', args=[self.post.id, self.comment.id])
        data = {
            "content": "수정된 댓글입니다."
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, data['content'])

    def test_update_comment_unauthorized(self):
        """다른 사용자의 댓글 수정 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('comment-detail', args=[self.post.id, self.comment.id])
        data = {
            "content": "수정된 댓글입니다."
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_comment(self):
        """댓글 삭제(소프트 딜리트) 테스트"""
        url = reverse('comment-detail', args=[self.post.id, self.comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_delete_comment_unauthorized(self):
        """다른 사용자의 댓글 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('comment-detail', args=[self.post.id, self.comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_comments(self):
        """댓글 목록 조회 테스트"""
        url = reverse('comment-list', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # setUp에서 생성한 댓글 1개

    def test_create_comment_unauthenticated(self):
        """인증되지 않은 사용자의 댓글 작성 시도 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse('comment-list', args=[self.post.id])
        data = {
            "content": "새로운 댓글입니다."
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
