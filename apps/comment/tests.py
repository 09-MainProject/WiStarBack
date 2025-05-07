from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.post.models import Post
from apps.user.models import User

from .models import Comment


class CommentTests(APITestCase):
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

        # 테스트용 댓글 데이터
        self.comment_data = {
            "content": "Test Comment",
        }

        # URL 설정
        self.comment_list_url = f"/api/posts/{self.post.id}/comments/"
        self.comment_detail_url = lambda pk: f"/api/posts/{self.post.id}/comments/{pk}/"

    def test_create_comment(self):
        """댓글 생성 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.comment_list_url,
            self.comment_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], self.comment_data["content"])
        self.assertEqual(response.data["author"]["nickname"], self.user.nickname)

    def test_create_comment_unauthenticated(self):
        """인증되지 않은 사용자의 댓글 생성 테스트"""
        response = self.client.post(
            self.comment_list_url,
            self.comment_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_comments(self):
        """댓글 목록 조회 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comment_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_comment(self):
        """댓글 상세 조회 테스트"""
        self.client.force_authenticate(user=self.user)
        # 댓글 생성
        comment = Comment.objects.create(
            content=self.comment_data["content"], post=self.post, author=self.user
        )

        # 댓글 조회
        response = self.client.get(self.comment_detail_url(comment.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], self.comment_data["content"])

    def test_update_comment(self):
        """댓글 수정 테스트"""
        self.client.force_authenticate(user=self.user)
        # 댓글 생성
        comment = Comment.objects.create(
            content=self.comment_data["content"], post=self.post, author=self.user
        )

        # 댓글 수정
        update_data = {"content": "Updated Comment"}
        response = self.client.patch(
            self.comment_detail_url(comment.id),
            update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], update_data["content"])

    def test_update_comment_unauthorized(self):
        """권한 없는 사용자의 댓글 수정 테스트"""
        self.client.force_authenticate(user=self.user)
        # 댓글 생성
        comment = Comment.objects.create(
            content=self.comment_data["content"], post=self.post, author=self.user
        )

        # 다른 사용자로 로그인
        self.client.force_authenticate(user=self.other_user)

        # 댓글 수정 시도
        update_data = {"content": "Updated Comment"}
        response = self.client.patch(
            self.comment_detail_url(comment.id),
            update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_comment(self):
        """댓글 삭제 테스트"""
        self.client.force_authenticate(user=self.user)
        # 댓글 생성
        comment = Comment.objects.create(
            content=self.comment_data["content"], post=self.post, author=self.user
        )

        # 댓글 삭제
        response = self.client.delete(self.comment_detail_url(comment.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_comment_unauthorized(self):
        """권한 없는 사용자의 댓글 삭제 테스트"""
        self.client.force_authenticate(user=self.user)
        # 댓글 생성
        comment = Comment.objects.create(
            content=self.comment_data["content"], post=self.post, author=self.user
        )

        # 다른 사용자로 로그인
        self.client.force_authenticate(user=self.other_user)

        # 댓글 삭제 시도
        response = self.client.delete(self.comment_detail_url(comment.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
