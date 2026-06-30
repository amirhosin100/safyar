import random
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import uuid
from django.core.cache import cache
from django.conf import settings


class Captcha:
    letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"

    @classmethod
    def _generate_captcha_text(cls, length=5):
        return ''.join(random.choices(cls.letters, k=length))

    @staticmethod
    def _generate_captcha_image(text):
        width, height = 170, 50
        bg_color = (255, 255, 255)
        image = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(settings.BASE_DIR / "static/fonts/Vazir-Bold.ttf", size=32)

        for i, char in enumerate(text):
            x = 15 + i * 25 + random.randint(-3, 3)
            y = random.randint(5, 15)
            color = (
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100)
            )
            draw.text((x, y), char, fill=color, font=font)

        # noise
        for _ in range(4):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=(
                random.randint(100, 180),
                random.randint(100, 180),
                random.randint(100, 180)
            ), width=1)

        # blur
        image = image.filter(ImageFilter.GaussianBlur(radius=0.8))

        # base64
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    @classmethod
    def create_captcha(cls, length=5):
        key = str(uuid.uuid4())
        text = cls._generate_captcha_text(length)
        image = cls._generate_captcha_image(text)

        cache.set(key, text, timeout=60)
        return {"captcha_key": key, "captcha_image": image}

    @staticmethod
    def check_captcha(captcha_key, text):
        value = cache.get(captcha_key)
        if not value or value != text:
            return False
        cache.delete(captcha_key)
        return True
