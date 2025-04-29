from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.post.models import Post, Comment

User = get_user_model()

class PostCommentTests(TestCase):
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
        print(f"Create post response: {response.content}")
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
        response = self.client.patch(url, data)  # PUT을 PATCH로 변경
        print(f"Update post response: {response.content}")
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

    def test_soft_delete_post(self):
        """게시글 소프트 삭제 메서드 테스트"""
        self.post.soft_delete(user=self.user)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)
        self.assertIsNotNone(self.post.deleted_at)
        self.assertEqual(self.post.deleted_by, self.user)

    def test_restore_post(self):
        """게시글 복구 메서드 테스트"""
        self.post.soft_delete(user=self.user)
        self.post.restore()
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_deleted)
        self.assertIsNone(self.post.deleted_at)
        self.assertIsNone(self.post.deleted_by)

    def test_create_comment(self):
        """댓글 생성 테스트"""
        url = reverse('comment-list-create', kwargs={'post_id': self.post.id})
        data = {
            "content": "댓글 내용입니다."
        }
        response = self.client.post(url, data)
        print(f"Create comment response: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author']['username'], self.user.username)

    def test_create_reply(self):
        """대댓글 생성 테스트"""
        parent_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="부모 댓글"
        )
        url = reverse('comment-list-create', kwargs={'post_id': self.post.id})
        data = {
            "content": "대댓글 내용입니다.",
            "parent": parent_comment.id
        }
        response = self.client.post(url, data)
        print(f"Create reply response: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent_comment.id)

    def test_retrieve_comment(self):
        """댓글 조회 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="댓글 조회 테스트"
        )
        url = reverse('comment-detail', kwargs={'post_id': self.post.id, 'pk': comment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], comment.content)

    def test_update_comment(self):
        """댓글 수정 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="수정 전 댓글"
        )
        url = reverse('comment-detail', kwargs={'post_id': self.post.id, 'pk': comment.id})
        data = {
            "content": "수정된 댓글"
        }
        response = self.client.patch(url, data)  # PUT을 PATCH로 변경
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "수정된 댓글")

    def test_update_comment_unauthorized(self):
        """다른 사용자의 댓글 수정 시도 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="수정 전 댓글"
        )
        self.client.force_authenticate(user=self.other_user)
        url = reverse('comment-detail', kwargs={'post_id': self.post.id, 'pk': comment.id})
        data = {
            "content": "수정된 댓글"
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_comment(self):
        """댓글 삭제(소프트 딜리트) 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="삭제할 댓글"
        )
        url = reverse('comment-detail', kwargs={'post_id': self.post.id, 'pk': comment.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

    def test_delete_comment_unauthorized(self):
        """다른 사용자의 댓글 삭제 시도 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="삭제할 댓글"
        )
        self.client.force_authenticate(user=self.other_user)
        url = reverse('comment-detail', kwargs={'post_id': self.post.id, 'pk': comment.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_comment(self):
        """댓글 소프트 삭제 메서드 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="댓글 소프트 삭제"
        )
        comment.soft_delete(user=self.user)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)
        self.assertIsNotNone(comment.deleted_at)
        self.assertEqual(comment.deleted_by, self.user)

    def test_restore_comment(self):
        """댓글 복구 메서드 테스트"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="댓글 복구"
        )
        comment.soft_delete(user=self.user)
        comment.restore()
        comment.refresh_from_db()
        self.assertFalse(comment.is_deleted)
        self.assertIsNone(comment.deleted_at)
        self.assertIsNone(comment.deleted_by)

    def test_comment_count(self):
        """게시글의 댓글 수 테스트"""
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content="댓글 1"
        )
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content="댓글 2"
        )
        url = reverse('post-detail', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comment_count'], 2)

    def test_search_comments(self):
        """댓글 검색 테스트"""
        # 테스트 댓글 생성
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content="첫 번째 댓글입니다."
        )
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content="두 번째 댓글입니다."
        )
        Comment.objects.create(
            post=self.post,
            author=self.other_user,
            content="다른 사용자의 댓글입니다."
        )

        # 내용으로 검색
        url = reverse('comment-list-create', kwargs={'post_id': self.post.id})
        response = self.client.get(f"{url}?content=첫 번째")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content'], "첫 번째 댓글입니다.")

        # 작성자로 필터링
        response = self.client.get(f"{url}?author={self.other_user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content'], "다른 사용자의 댓글입니다.")