from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.post.models import Post
from apps.user.models import User

from .models import Comment

User = get_user_model()


class CommentTests(APITestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="test@test.com",
            password="test1234",
            name="테스터",
            nickname="tester",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            name="Other User",
            nickname="otheruser",
        )

        # 테스트용 게시물 생성
        self.post = Post.objects.create(
            title="테스트 게시글",
            content="내용입니다.",
            author=self.user,
        )

        # 테스트용 댓글 데이터
        self.comment_data = {
            "content": "부모 댓글",
        }

        # URL 설정
        self.comment_list_url = reverse(
            "comment-list", kwargs={"post_id": self.post.id}
        )
        self.comment_detail_url = lambda pk: reverse(
            "comment-detail", kwargs={"post_id": self.post.id, "pk": pk}
        )

        self.client.force_authenticate(user=self.user)
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, content="부모 댓글"
        )

    def test_create_comment(self):
        """댓글 생성 테스트"""
        data = {"content": "댓글입니다."}
        response = self.client.post(self.comment_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_comment_unauthenticated(self):
        """인증되지 않은 사용자의 댓글 생성 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.comment_list_url,
            self.comment_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_comments(self):
        """댓글 목록 조회 테스트"""
        response = self.client.get(self.comment_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_comment(self):
        """댓글 상세 조회 테스트"""
        response = self.client.get(self.comment_detail_url(self.comment.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], self.comment_data["content"])

    def test_update_comment(self):
        """댓글 수정 테스트"""
        data = {"content": "수정된 댓글"}
        response = self.client.patch(
            self.comment_detail_url(self.comment.id),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], data["content"])

    def test_update_comment_unauthorized(self):
        """권한 없는 사용자의 댓글 수정 테스트"""
        self.client.force_authenticate(user=self.other_user)
        data = {"content": "Updated Comment"}
        response = self.client.patch(
            self.comment_detail_url(self.comment.id),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_comment(self):
        """댓글 삭제 테스트"""
        response = self.client.delete(self.comment_detail_url(self.comment.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_comment_unauthorized(self):
        """권한 없는 사용자의 댓글 삭제 테스트"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.comment_detail_url(self.comment.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reply(self):
        """대댓글 생성 테스트"""
        data = {"content": "대댓글입니다.", "parent": self.comment.id}
        response = self.client.post(self.comment_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["parent"], self.comment.id)

    def test_create_nested_reply(self):
        """대댓글에 대한 답글 생성 시도 테스트 (실패해야 함)"""
        reply = Comment.objects.create(
            post=self.post, author=self.user, content="대댓글", parent=self.comment
        )
        data = {"content": "Nested Reply", "parent": reply.id}
        response = self.client.post(self.comment_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_comments_with_replies(self):
        """댓글과 대댓글 목록 조회 테스트"""
        response = self.client.get(self.comment_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            len(response.data["results"]) > 0
        )  # 응답 데이터가 비어있지 않은지 확인
        for comment in response.data["results"]:
            self.assertIn("replies", comment)  # 각 댓글에 'replies' 필드가 있는지 확인
            self.assertIsInstance(comment["replies"], list)
