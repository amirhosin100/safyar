from django.urls import reverse


def get_detail_url_resolver(app_name: str, model_name: str):
    """
    Returns a function that resolves the detail URL for a given model name and app name.
    """

    def resolve_detail_url(pk):
        """
        Resolves the detail URL using the app_name, model_name, and provided pk.
        """
        return reverse(f"{app_name}-{model_name}-detail", args=(pk,))

    return resolve_detail_url
