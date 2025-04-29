from rest_framework.pagination import PageNumberPagination
from django.conf import settings

class PostPagination(PageNumberPagination):
    """
    게시물 목록 페이지네이션
    
    Attributes:
        page_size (int): 한 페이지에 표시할 게시물 수
        page_size_query_param (str): 페이지 크기를 지정하는 쿼리 파라미터
        max_page_size (int): 최대 페이지 크기
    """
    page_size = getattr(settings, 'POST_PAGE_SIZE', 10)
    page_size_query_param = 'page_size'
    max_page_size = getattr(settings, 'POST_MAX_PAGE_SIZE', 100)


class CommentPagination(PageNumberPagination):
    """
    댓글 목록 페이지네이션
    
    Attributes:
        page_size (int): 한 페이지에 표시할 댓글 수
        page_size_query_param (str): 페이지 크기를 지정하는 쿼리 파라미터
        max_page_size (int): 최대 페이지 크기
    """
    page_size = getattr(settings, 'COMMENT_PAGE_SIZE', 20)
    page_size_query_param = 'page_size'
    max_page_size = getattr(settings, 'COMMENT_MAX_PAGE_SIZE', 100)