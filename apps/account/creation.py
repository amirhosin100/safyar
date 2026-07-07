from apps.smoothing.models import Smoothing

def create_smoothing(user):
    if user.smoothing is None:
        data = {
            "phone_number": user.phone_number,
            "owner_name": user.full_name,
        }
        if hasattr(user, "request"):
            data["address"] = user.request.address
            data["name"] = user.request.shop_name

        smoothing = Smoothing.objects.create(**data)
        user.smoothing = smoothing