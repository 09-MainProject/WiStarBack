import io
import os
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image



def process_image(image_file: UploadedFile) -> UploadedFile:
    """
    이미지 파일을 처리합니다.
    - 이미지 크기 조정
    - WebP 포맷으로 변환
    - 이미지 품질 최적화
    """
    # 이미지 열기
    img = Image.open(image_file)

    # 이미지가 RGBA 모드인 경우 RGB로 변환
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background

    # 이미지 크기 조정 (최대 1920x1080)
    max_size = (1920, 1080)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # 이미지를 바이트로 변환
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=85, method=6)  # method=6은 최고 압축률
    output.seek(0)

    # 파일명 생성 (WebP 확장자로 변경)
    filename = os.path.splitext(image_file.name)[0] + ".webp"

    # UploadedFile 객체 생성
    return UploadedFile(file=output, name=filename, content_type="image/webp")


def process_image_old(image_file):
    """
    이미지 파일을 처리하여 WebP 형식으로 변환하고 크기를 조정합니다.

    Args:
        image_file: 이미지 파일 또는 BytesIO 객체

    Returns:
        ContentFile: 처리된 이미지 파일
    """
    try:
        # 이미지 열기
        img = Image.open(image_file)

        # 이미지가 RGBA 모드인 경우 RGB로 변환
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background

        # 이미지 크기 조정
        if max(img.size) > settings.IMAGE_MAX_SIZE:
            ratio = settings.IMAGE_MAX_SIZE / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # WebP로 변환
        output = BytesIO()
        img.save(output, format="WEBP", quality=settings.IMAGE_QUALITY)
        output.seek(0)

        # 파일명 생성
        if hasattr(image_file, "name"):
            filename = os.path.splitext(image_file.name)[0] + ".webp"
        else:
            filename = f"processed_{os.urandom(8).hex()}.webp"

        # ContentFile로 변환하여 반환
        return ContentFile(output.getvalue(), name=filename)
    except Exception as e:
        print(f"이미지 처리 중 오류 발생: {e}")
        raise
