from django.conf import settings

from apps.core.access_views import generate_identify


def make_url(endpoint):
    protocol = settings.DEFAULT_PROTOCOL
    host = settings.SITE_URL

    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    return f"{protocol}://{host}/{endpoint}"


def create_detail_project_url(project):
    code = generate_identify(project)
    endpoint = settings.PROJECT_DETAIL_URL.format(identify_code=code)
    return make_url(endpoint)
