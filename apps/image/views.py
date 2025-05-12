from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageUploadSerializer

class ImageUploadView(APIView):
    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            image = serializer.save()
            return Response({
                "image_url": image.image_url,
                "thumbnail_url": image.get_thumbnail_url(),
                "public_id": image.public_id,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = ImageUploadSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            image = serializer.update(None, serializer.validated_data)
            return Response({
                "image_url": image.image_url,
                "thumbnail_url": image.get_thumbnail_url(),
                "public_id": image.public_id,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            deleted_count = serializer.delete()
            return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)