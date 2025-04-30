from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from apps.post.models import Post

User = get_user_model()


class PostTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="password123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

        self.post = Post.objects.create(
            title="Test Post", content="This is a test post.", author=self.user
        )

    def test_create_post(self):
        """게시글 생성 테스트"""
        url = reverse("post-list")
        data = {"title": "새 게시글", "content": "새 게시글 내용입니다."}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], data["title"])

    def test_retrieve_post(self):
        """게시글 조회 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post.title)

    def test_update_post(self):
        """게시글 수정 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        data = {
            "title": "수정된 제목",
            "content": "이것은 수정된 게시글의 내용입니다. 10자 이상으로 작성했습니다.",
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "수정된 제목")

    def test_update_post_unauthorized(self):
        """다른 사용자의 게시글 수정 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", args=[self.post.id])
        data = {
            "title": "수정된 제목",
            "content": "이것은 수정된 게시글의 내용입니다. 10자 이상으로 작성했습니다.",
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post(self):
        """게시글 삭제(소프트 딜리트) 테스트"""
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_delete_post_by_admin(self):
        """관리자의 게시글 삭제 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_delete_post_unauthorized(self):
        """다른 사용자의 게시글 삭제 시도 테스트"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("post-detail", args=[self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_increase_post_views(self):
        """게시글 조회수 증가 테스트"""
        url = reverse("post-increase-views", args=[self.post.id])
        original_views = self.post.views
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, original_views + 1)

    def test_create_post_with_image(self):
        """이미지가 포함된 게시글 생성 테스트"""
        url = reverse("post-list")
        # 테스트용 이미지 파일 생성
        image = Image.new("RGB", (100, 100), color="white")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_file = SimpleUploadedFile(
            name="test_image.jpg", content=image_io.read(), content_type="image/jpeg"
        )

        data = {
            "title": "이미지가 있는 게시글",
            "content": "이미지가 포함된 게시글 내용입니다. 10자 이상으로 작성했습니다.",
            "image": image_file,
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["image"])
        self.assertEqual(response.data["title"], "이미지가 있는 게시글")

    def test_create_post_with_invalid_image(self):
        """잘못된 이미지로 게시글 생성 시도 테스트"""
        url = reverse("post-list")
        # 잘못된 형식의 파일 생성
        invalid_file = SimpleUploadedFile(
            name="test.txt", content=b"This is not an image", content_type="text/plain"
        )
        data = {
            "title": "잘못된 이미지 게시글",
            "content": "잘못된 이미지가 포함된 게시글 내용입니다. 10자 이상으로 작성했습니다.",
            "image": invalid_file,
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_posts(self):
        """게시글 목록 조회 테스트"""
        # 추가 게시글 생성
        Post.objects.create(
            title="Another Post", content="This is another test post.", author=self.user
        )

        url = reverse("post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 2
        )  # setUp에서 생성한 게시글 1개 + 추가 게시글 1개

    def test_list_posts_with_search(self):
        """게시글 검색 테스트"""
        # 검색할 게시글 생성
        Post.objects.create(
            title="Searchable Post",
            content="This is a searchable post.",
            author=self.user,
        )

        url = reverse("post-list")
        response = self.client.get(url, {"search": "Searchable"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Searchable Post")

    def test_list_posts_with_filter(self):
        """게시글 필터링 테스트"""
        # 필터링할 게시글 생성
        Post.objects.create(
            title="Filtered Post", content="This is a filtered post.", author=self.user
        )

        url = reverse("post-list")
        response = self.client.get(url, {"title": "Filtered"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Filtered Post")

    def test_list_posts_with_ordering(self):
        """게시글 정렬 테스트"""
        # 정렬할 게시글 생성
        Post.objects.create(
            title="Newer Post", content="This is a newer post.", author=self.user
        )

        url = reverse("post-list")
        response = self.client.get(url, {"ordering": "created_at"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(
            response.data["results"][0]["title"], "Test Post"
        )  # 첫 번째 게시글
        self.assertEqual(
            response.data["results"][1]["title"], "Newer Post"
        )  # 두 번째 게시글

    def test_partial_update_post(self):
        """게시글 부분 수정 테스트"""
        url = reverse("post-detail", args=[self.post.id])

        # 제목만 수정
        data = {"title": "제목만 수정"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "제목만 수정")
        self.assertEqual(self.post.content, "This is a test post.")  # 내용은 그대로

        # 내용만 수정
        data = {"content": "내용만 수정했습니다."}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "제목만 수정")  # 제목은 그대로
        self.assertEqual(self.post.content, "내용만 수정했습니다.")

        # 이미지만 수정
        image = Image.new("RGB", (100, 100), color="white")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_file = SimpleUploadedFile(
            name="new_image.jpg", content=image_io.read(), content_type="image/jpeg"
        )

        data = {"image": image_file}
        response = self.client.patch(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertIsNotNone(self.post.image)
        self.assertEqual(self.post.title, "제목만 수정")  # 제목은 그대로
        self.assertEqual(self.post.content, "내용만 수정했습니다.")  # 내용은 그대로
