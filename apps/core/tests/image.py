from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def create_image(name="test"):
    img = Image.new("RGB", (20, 20), color=(255, 255, 255))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return ContentFile(buffer.read(), name + ".png")
