import json
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("=" * 50)
        print(f"{request.method} {request.path}")

        if request.body:
            try:
                body = request.body.decode("utf-8")
                print(body)

                # اگر JSON بود
                try:
                    print(json.loads(body))
                except json.JSONDecodeError:
                    pass

            except UnicodeDecodeError:
                print("<Binary Data>")

        response = self.get_response(request)
        print(response.content)
        return response
