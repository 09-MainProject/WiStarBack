from rest_framework import serializers
from .models import Comment
from apps.user.serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):
    """댓글 시리얼라이저"""
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'updated_at', 'is_deleted']
        read_only_fields = ['author', 'created_at', 'updated_at', 'is_deleted']

class CommentCreateSerializer(serializers.ModelSerializer):
    """댓글 생성 시리얼라이저"""
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['content', 'author']
        read_only_fields = ['author']

class CommentUpdateSerializer(serializers.ModelSerializer):
    """댓글 수정 시리얼라이저"""
    class Meta:
        model = Comment
        fields = ['content'] 